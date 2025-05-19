#!/usr/bin/env python
"""
Job Worker Service

This script runs a dedicated job worker service that processes background jobs from Redis queues.
It's designed to be started as a separate process from the main application server.

Key features:
- Connects to Redis using SSL for Azure Redis Cache
- Supports multiple worker processes
- Can be configured to listen on specific queues
- Handles graceful shutdown with signal handlers
- Provides detailed logging of worker activities
"""

import os
import sys
import time
import signal
import logging
import argparse
from redis import Redis
import ssl
from rq import Worker, Queue, Connection
from redis.connection import SSLConnection, ConnectionPool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('job_worker.log')
    ]
)
logger = logging.getLogger(__name__)

# Redis connection parameters
REDIS_HOST = 'my-bullmq-cache.redis.cache.windows.net'
REDIS_PORT = 6380
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
REDIS_SSL = True

def get_redis_connection():
    """Get a connection to Redis using SSL for Azure Redis Cache"""
    try:
        # Configure SSL connection for Azure Redis Cache
        import ssl
        
        # Use SSL connection via ConnectionPool
        pool = ConnectionPool(
            connection_class=SSLConnection,
            host=REDIS_HOST,
            port=int(REDIS_PORT),
            password=REDIS_PASSWORD,
            socket_timeout=10,
            socket_connect_timeout=10,
            health_check_interval=30,
            ssl_cert_reqs=ssl.CERT_NONE
        )
        conn = Redis(connection_pool=pool, decode_responses=False)
        
        # Test the connection
        conn.ping()
        logger.info(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        raise

def setup_worker(queues=None, worker_id=None):
    """Set up a worker process to listen on specified queues"""
    if queues is None:
        queues = ['high', 'default', 'low', 'email', 'indexing']
    
    worker_name = f"worker{worker_id}" if worker_id else None
    
    # Get Redis connection
    redis_conn = get_redis_connection()
    
    # Create queue objects
    queue_objects = [Queue(queue_name, connection=redis_conn) for queue_name in queues]
    
    # Create and return worker
    worker = Worker(
        queues=queue_objects, 
        name=worker_name,
        connection=redis_conn
    )
    
    return worker, redis_conn

def start_worker_service(num_workers=1, queues=None, burst_mode=False):
    """
    Start the worker service with the specified number of workers and queues
    
    Args:
        num_workers: Number of worker processes to start (default: 1)
        queues: List of queue names to process (default: ['high', 'default', 'low', 'email', 'indexing'])
        burst_mode: Whether to run in burst mode (process existing jobs then exit)
    """
    logger.info(f"Starting job worker service with {num_workers} workers")
    logger.info(f"Processing queues: {', '.join(queues or ['high', 'default', 'low', 'email', 'indexing'])}")
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down workers...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Set up connection
    redis_conn = get_redis_connection()
    
    with Connection(redis_conn):
        if num_workers == 1:
            # Single worker mode
            worker, _ = setup_worker(queues)
            logger.info(f"Starting worker {worker.name}")
            worker.work(burst=burst_mode)
        else:
            # Multi-worker mode - start separately configurable workers
            workers = []
            
            # Create workers for each queue group
            for i in range(num_workers):
                worker_name = f"worker{i+1}"
                logger.info(f"Starting worker {worker_name}")
                
                # For multi-worker setups, you can customize which queues each worker listens to
                # For example, dedicate some workers to high-priority queues
                if i == 0 and num_workers > 2:
                    # First worker focuses on high-priority queues
                    worker_queues = ['high']
                elif i == 1 and num_workers > 2:
                    # Second worker focuses on email queue
                    worker_queues = ['email']
                else:
                    # Other workers handle all queues with balanced load
                    worker_queues = queues or ['high', 'default', 'low', 'email', 'indexing']
                
                worker, _ = setup_worker(worker_queues, i+1)
                workers.append(worker)
                worker.work(burst=burst_mode)
    
    logger.info("All workers have exited")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run Redis Queue workers for background job processing')
    
    parser.add_argument(
        '--workers', 
        type=int, 
        default=1, 
        help='Number of worker processes to start (default: 1)'
    )
    
    parser.add_argument(
        '--queues', 
        type=str, 
        default='high,default,low,email,indexing', 
        help='Comma-separated list of queue names to process (default: high,default,low,email,indexing)'
    )
    
    parser.add_argument(
        '--burst', 
        action='store_true', 
        help='Run in burst mode - process existing jobs then exit'
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    # Parse arguments
    args = parse_arguments()
    
    # Convert comma-separated queue string to list
    queue_list = [q.strip() for q in args.queues.split(',') if q.strip()]
    
    try:
        # Start the worker service
        start_worker_service(
            num_workers=args.workers,
            queues=queue_list,
            burst_mode=args.burst
        )
    except KeyboardInterrupt:
        logger.info("Interrupted by user, shutting down...")
    except Exception as e:
        logger.error(f"Error in worker service: {str(e)}", exc_info=True)
        sys.exit(1)