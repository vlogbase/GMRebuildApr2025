"""
Singleton Background Worker

This module implements a singleton background service that handles system-wide tasks
using Redis-based distributed locks to ensure only one instance runs across the entire
autoscaling cluster. This prevents redundant API calls and resource contention.
"""

import os
import time
import logging
import threading
import signal
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SingletonBackgroundWorker:
    """
    Manages singleton background tasks across multiple application instances
    using Redis distributed locks.
    """
    
    def __init__(self):
        self.redis_client = None
        self.running = False
        self.worker_thread = None
        self.shutdown_event = threading.Event()
        
        # Task configuration
        self.tasks = {
            'price_update': {
                'interval_hours': 3,
                'lock_key': 'singleton:price_update',
                'lock_ttl': 3600,  # 1 hour lock TTL
                'function': self._update_model_prices,
                'last_run': None
            }
        }
        
    def _get_redis_client(self):
        """Get Redis client with connection handling"""
        if self.redis_client is None:
            try:
                from api_cache import get_redis_client
                self.redis_client = get_redis_client()
                if self.redis_client:
                    logger.info("Redis client connected for singleton worker")
                else:
                    logger.warning("Redis not available - singleton tasks may not coordinate properly")
            except Exception as e:
                logger.warning(f"Could not connect to Redis: {e}")
                
        return self.redis_client
    
    def _acquire_distributed_lock(self, lock_key: str, ttl: int = 3600) -> bool:
        """
        Acquire a distributed lock using Redis SET with NX and EX options.
        
        Args:
            lock_key: Unique lock identifier
            ttl: Time-to-live in seconds
            
        Returns:
            bool: True if lock acquired, False otherwise
        """
        redis_client = self._get_redis_client()
        if not redis_client:
            # If Redis is not available, allow the task to run
            # This prevents the application from being completely blocked
            logger.warning(f"Redis unavailable - allowing task {lock_key} to proceed")
            return True
            
        try:
            # SET key value NX EX ttl - atomic operation
            # NX = Only set if key doesn't exist
            # EX = Set expiration time
            worker_id = f"{os.getpid()}_{threading.current_thread().ident}"
            result = redis_client.set(lock_key, worker_id, nx=True, ex=ttl)
            
            if result:
                logger.info(f"Acquired distributed lock: {lock_key} (worker: {worker_id})")
                return True
            else:
                # Check who has the lock for debugging
                current_holder = redis_client.get(lock_key)
                if current_holder:
                    logger.debug(f"Lock {lock_key} held by: {current_holder.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error acquiring distributed lock {lock_key}: {e}")
            return False
    
    def _release_distributed_lock(self, lock_key: str):
        """Release a distributed lock"""
        redis_client = self._get_redis_client()
        if not redis_client:
            return
            
        try:
            worker_id = f"{os.getpid()}_{threading.current_thread().ident}"
            
            # Use Lua script for atomic check-and-delete
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            
            result = redis_client.eval(lua_script, 1, lock_key, worker_id)
            if result == 1:
                logger.info(f"Released distributed lock: {lock_key}")
            else:
                logger.warning(f"Could not release lock {lock_key} - not owned by this worker")
                
        except Exception as e:
            logger.error(f"Error releasing distributed lock {lock_key}: {e}")
    
    def _update_model_prices(self) -> Dict[str, Any]:
        """
        Update model prices from OpenRouter API and populate Redis cache.
        This is the main singleton task that should only run on one instance.
        """
        start_time = time.time()
        logger.info("Starting singleton model price update task")
        
        try:
            # Import price updater functions
            from price_updater import fetch_and_store_openrouter_prices, _populate_redis_pricing_cache
            
            # Step 1: Fetch and store prices from OpenRouter API
            logger.info("Fetching model prices from OpenRouter API...")
            fetch_success = fetch_and_store_openrouter_prices(force_update=True)
            
            if not fetch_success:
                return {
                    'success': False,
                    'error': 'Failed to fetch prices from OpenRouter API',
                    'duration': time.time() - start_time
                }
            
            logger.info("✓ Model prices fetched and stored in database")
            
            # Step 2: Populate Redis cache with database data
            logger.info("Populating Redis cache with updated pricing data...")
            _populate_redis_pricing_cache()
            logger.info("✓ Redis cache populated with latest pricing data")
            
            duration = time.time() - start_time
            
            # Update last run time
            self.tasks['price_update']['last_run'] = datetime.utcnow()
            
            logger.info(f"🎉 Singleton price update completed successfully in {duration:.2f}s")
            
            return {
                'success': True,
                'duration': duration,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error in singleton price update: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration': duration
            }
    
    def _should_run_task(self, task_name: str) -> bool:
        """Check if a task should run based on its schedule"""
        task_config = self.tasks.get(task_name)
        if not task_config:
            return False
            
        last_run = task_config.get('last_run')
        if not last_run:
            return True  # Never run before
            
        interval_hours = task_config.get('interval_hours', 3)
        next_run_time = last_run + timedelta(hours=interval_hours)
        
        return datetime.utcnow() >= next_run_time
    
    def _run_singleton_task(self, task_name: str):
        """Run a singleton task with distributed locking"""
        task_config = self.tasks.get(task_name)
        if not task_config:
            logger.error(f"Unknown task: {task_name}")
            return
            
        lock_key = task_config['lock_key']
        lock_ttl = task_config['lock_ttl']
        task_function = task_config['function']
        
        # Try to acquire the distributed lock
        if not self._acquire_distributed_lock(lock_key, lock_ttl):
            logger.debug(f"Could not acquire lock for {task_name} - another instance is running it")
            return
            
        try:
            # Run the task
            logger.info(f"Executing singleton task: {task_name}")
            result = task_function()
            
            if result.get('success'):
                logger.info(f"✓ Singleton task {task_name} completed successfully")
            else:
                logger.error(f"✗ Singleton task {task_name} failed: {result.get('error', 'Unknown error')}")
                
        finally:
            # Always release the lock
            self._release_distributed_lock(lock_key)
    
    def _worker_loop(self):
        """Main worker loop that runs singleton tasks"""
        logger.info("Singleton background worker started")
        
        while not self.shutdown_event.is_set():
            try:
                # Check each task
                for task_name in self.tasks.keys():
                    if self.shutdown_event.is_set():
                        break
                        
                    if self._should_run_task(task_name):
                        self._run_singleton_task(task_name)
                
                # Sleep for 60 seconds between checks
                self.shutdown_event.wait(60)
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                # Sleep for 30 seconds before retrying
                self.shutdown_event.wait(30)
        
        logger.info("Singleton background worker stopped")
    
    def start(self):
        """Start the singleton background worker"""
        if self.running:
            logger.warning("Singleton worker already running")
            return
            
        self.running = True
        self.shutdown_event.clear()
        
        # Start worker thread
        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            name="singleton-worker",
            daemon=True  # Allow main process to exit
        )
        self.worker_thread.start()
        
        logger.info("Singleton background worker started successfully")
    
    def stop(self):
        """Stop the singleton background worker"""
        if not self.running:
            return
            
        logger.info("Stopping singleton background worker...")
        self.running = False
        self.shutdown_event.set()
        
        # Wait for worker thread to finish
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=10)
            
        logger.info("Singleton background worker stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the singleton worker"""
        status = {
            'running': self.running,
            'redis_connected': self._get_redis_client() is not None,
            'tasks': {}
        }
        
        for task_name, task_config in self.tasks.items():
            last_run = task_config.get('last_run')
            status['tasks'][task_name] = {
                'last_run': last_run.isoformat() if last_run else None,
                'should_run': self._should_run_task(task_name),
                'interval_hours': task_config.get('interval_hours')
            }
            
        return status

# Global singleton worker instance
_singleton_worker = None

def get_singleton_worker() -> SingletonBackgroundWorker:
    """Get the global singleton worker instance"""
    global _singleton_worker
    if _singleton_worker is None:
        _singleton_worker = SingletonBackgroundWorker()
    return _singleton_worker

def start_singleton_worker():
    """Start the singleton background worker"""
    worker = get_singleton_worker()
    worker.start()
    return worker

def stop_singleton_worker():
    """Stop the singleton background worker"""
    global _singleton_worker
    if _singleton_worker:
        _singleton_worker.stop()

# CLI interface
def main():
    """CLI entry point for running the singleton worker"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run singleton background worker')
    parser.add_argument('--status', action='store_true', help='Show worker status')
    parser.add_argument('--run-once', action='store_true', help='Run price update once and exit')
    
    args = parser.parse_args()
    
    if args.status:
        worker = get_singleton_worker()
        status = worker.get_status()
        print(f"Worker Status: {'Running' if status['running'] else 'Stopped'}")
        print(f"Redis Connected: {status['redis_connected']}")
        for task_name, task_status in status['tasks'].items():
            print(f"\nTask: {task_name}")
            print(f"  Last Run: {task_status['last_run'] or 'Never'}")
            print(f"  Should Run: {task_status['should_run']}")
            print(f"  Interval: {task_status['interval_hours']} hours")
        return
    
    if args.run_once:
        worker = get_singleton_worker()
        worker._run_singleton_task('price_update')
        return
    
    # Run as daemon
    worker = start_singleton_worker()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        stop_singleton_worker()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        stop_singleton_worker()

if __name__ == "__main__":
    main()