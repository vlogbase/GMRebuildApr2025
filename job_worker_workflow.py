#!/usr/bin/env python
"""
Job Worker Workflow

This script is designed to be run in a Replit workflow to process background jobs.
It sets up and runs a Redis Queue worker that processes jobs from specified queues.
"""

import os
import sys
import logging
import time
import signal
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'worker_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger('job_worker_workflow')

try:
    from rq import Worker, Queue, Connection
    from redis import Redis
    from redis.exceptions import RedisError
    from redis_cache import get_redis_connection
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    logger.error("Make sure rq, redis and other dependencies are installed")
    sys.exit(1)

def parse_args():
    """Parse command line arguments from environment variable or command line"""
    # If arguments are provided in environment variable, use those
    if 'WORKER_ARGS' in os.environ:
        # Split string into list of arguments
        worker_args = os.environ.get('WORKER_ARGS', '').split()
        logger.info(f"Using worker arguments from environment: {worker_args}")
        sys.argv.extend(worker_args)
    
    parser = argparse.ArgumentParser(description="Start RQ worker in a Replit workflow")
    parser.add_argument('--queues', help='Comma-separated list of queue names to work on')
    parser.add_argument('--name', help='Worker name (default: hostname:pid)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    parser.add_argument('--burst', action='store_true', help='Run in burst mode (quit after all work is done)')
    
    return parser.parse_args()

def setup_signal_handlers(worker):
    """Set up signal handlers for graceful shutdown"""
    def handle_shutdown_signal(signum, frame):
        logger.info(f"Received signal {signum}, shutting down worker...")
        if worker:
            worker.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)

def run_worker(queues=None, name=None, burst=False):
    """Run a Redis Queue worker"""
    try:
        # Get Redis connection
        redis_conn = get_redis_connection()
        if not redis_conn:
            logger.error("Failed to get Redis connection")
            return False
        
        # Default queue names if not specified
        if not queues:
            queues = ['high', 'default', 'low', 'email', 'indexing']
        
        logger.info(f"Starting worker to process queues: {queues}")
        
        with Connection(redis_conn):
            worker = Worker(
                queues=queues,
                name=name,
                log_job_description=True
            )
            
            # Set up signal handlers
            setup_signal_handlers(worker)
            
            # Start worker
            logger.info(f"Worker {worker.name} starting")
            worker.work(burst=burst)
            
            # If we get here with burst=False, something went wrong
            if not burst:
                logger.error("Worker exited unexpectedly")
                return False
            
            logger.info("Worker completed all jobs (burst mode)")
            return True
    
    except RedisError as e:
        logger.error(f"Redis error: {e}")
        return False
    
    except Exception as e:
        logger.error(f"Error running worker: {e}")
        logger.exception("Stack trace:")
        return False

def main():
    """Main entry point"""
    try:
        args = parse_args()
        
        # Set logging level
        logging.getLogger().setLevel(getattr(logging, args.log_level))
        
        # Parse queue names
        queues = args.queues.split(',') if args.queues else None
        
        # Collect Redis connection info
        redis_info = {}
        try:
            conn = get_redis_connection()
            if conn:
                info = conn.info()
                redis_info = {
                    'version': info.get('redis_version', 'Unknown'),
                    'uptime': info.get('uptime_in_seconds', 0),
                    'clients': info.get('connected_clients', 0),
                    'memory': info.get('used_memory_human', 'Unknown')
                }
                logger.info(f"Redis connection established - version: {redis_info['version']}, "
                           f"memory: {redis_info['memory']}")
            else:
                logger.warning("Could not get Redis connection info")
        except Exception as e:
            logger.warning(f"Error getting Redis info: {e}")
        
        # Run worker
        logger.info(f"Starting job worker in {'burst' if args.burst else 'continuous'} mode")
        success = run_worker(
            queues=queues,
            name=args.name,
            burst=args.burst
        )
        
        if success:
            logger.info("Worker completed successfully")
            return 0
        else:
            logger.error("Worker failed")
            return 1
    
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        logger.exception("Stack trace:")
        return 1

if __name__ == "__main__":
    sys.exit(main())