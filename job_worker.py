"""
Job Worker Module

This module implements a worker for the Redis-backed job system.
It's designed to be run as a separate process to handle background tasks.
"""

import os
import sys
import time
import signal
import logging
import traceback
from typing import List, Optional, Dict, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('job_worker.log')
    ]
)
logger = logging.getLogger('job_worker')

# Import RQ
try:
    import redis
    from redis import Redis
    from rq import Worker, Queue, Connection
    from rq.worker import SimpleWorker, HerokuWorker
    from rq.job import Job
except ImportError:
    logger.error("RQ not installed. Please install with: pip install rq")
    redis = None
    Worker = None
    Queue = None
    Connection = None
    SimpleWorker = None
    HerokuWorker = None

# Import Redis cache
from redis_cache import get_redis_connection

def run_worker(queue_names: List[str] = None, 
              burst: bool = False, 
              name: str = None,
              worker_ttl: int = 420,
              worker_class: str = "default") -> int:
    """
    Run a worker process
    
    Args:
        queue_names: Queue names to listen to (default: ['default'])
        burst: Run in burst mode (process existing jobs and exit)
        name: Worker name (default: auto-generated)
        worker_ttl: Worker timeout in seconds (default: 420)
        worker_class: Worker class to use (default, simple, heroku)
        
    Returns:
        int: Exit code
    """
    # Check if RQ is available
    if Worker is None or Queue is None:
        logger.error("RQ not available")
        return 1
    
    # Default queue names
    if queue_names is None or len(queue_names) == 0:
        queue_names = ['default']
    
    # Get Redis connection
    redis_conn = get_redis_connection()
    if redis_conn is None:
        logger.error("Could not connect to Redis")
        return 1
    
    try:
        # Create queues
        queues = [Queue(queue_name, connection=redis_conn) for queue_name in queue_names]
        
        # Log the queues
        logger.info(f"Listening to queues: {', '.join(queue_names)}")
        
        # Set up worker
        if worker_class.lower() == 'simple':
            worker_cls = SimpleWorker
        elif worker_class.lower() == 'heroku':
            worker_cls = HerokuWorker
        else:
            worker_cls = Worker
        
        # Create worker with connection context
        with Connection(redis_conn):
            worker = worker_cls(
                queues,
                name=name,
                default_worker_ttl=worker_ttl
            )
            
            # Set up signal handlers
            def handle_shutdown_signal(signum, frame):
                worker.shutdown_requested = True
                logger.info(f"Shutdown requested (signal: {signum})")
            
            signal.signal(signal.SIGINT, handle_shutdown_signal)
            signal.signal(signal.SIGTERM, handle_shutdown_signal)
            
            # Start worker
            worker.work(burst=burst)
            
            return 0
    
    except Exception as e:
        logger.error(f"Error running worker: {e}")
        logger.error(traceback.format_exc())
        return 1

def start_worker(queues: List[str] = None, burst: bool = False):
    """
    Simple entry point function for starting a worker
    
    Args:
        queues: Queue names to listen to
        burst: Run in burst mode
        
    Returns:
        None
    """
    exit_code = run_worker(queue_names=queues, burst=burst)
    sys.exit(exit_code)

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Run a Redis Queue worker')
    parser.add_argument(
        'queues',
        nargs='*',
        default=['default'],
        help='Queues to listen on (default: default)'
    )
    parser.add_argument(
        '--burst',
        action='store_true',
        help='Run in burst mode (process jobs and exit)'
    )
    parser.add_argument(
        '--name',
        type=str,
        default=None,
        help='Worker name'
    )
    parser.add_argument(
        '--worker-ttl',
        type=int,
        default=420,
        help='Worker TTL in seconds (default: 420)'
    )
    
    args = parser.parse_args()
    
    # Start worker
    start_worker(queues=args.queues, burst=args.burst)