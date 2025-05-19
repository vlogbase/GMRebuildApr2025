#!/usr/bin/env python
"""
Job Worker

This script starts a Redis Queue worker that processes jobs from one or more queues.
It can be run from the command line with arguments specifying which queues to work on.

Example usage:
    python job_worker.py high default low  # Work on high, default, and low queues
    python job_worker.py --name worker1 high  # Named worker for high priority queue
    python job_worker.py --burst  # Process all waiting jobs and exit
"""

import os
import sys
import logging
import signal
import argparse
from redis import Redis
from rq import Worker, Queue, Connection
from redis_cache import get_redis_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('job_worker')

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Start a Redis Queue worker")
    
    # Positional argument for queue names (can be multiple)
    parser.add_argument('queues', nargs='*', help='Queue names to process')
    
    # Optional arguments
    parser.add_argument('--name', help='Worker name (default: hostname:pid)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    parser.add_argument('--burst', action='store_true', help='Run in burst mode (quit after all work is done)')
    
    return parser.parse_args()

def setup_signal_handlers(worker):
    """Set up signal handlers for graceful shutdown"""
    def handle_signal(signum, frame):
        logger.info(f"Received signal {signum}, shutting down worker...")
        if worker:
            worker.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

def main():
    """Main entry point"""
    args = parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Get queue names from args, default to all standard queues if none specified
    queue_names = args.queues if args.queues else ['high', 'default', 'low', 'email', 'indexing']
    
    # Get Redis connection
    redis_connection = get_redis_connection()
    if not redis_connection:
        logger.error("Could not establish Redis connection")
        return 1
    
    logger.info(f"Starting worker for queues: {', '.join(queue_names)}")
    
    try:
        with Connection(redis_connection):
            # Create worker
            worker = Worker(
                queues=[Queue(name) for name in queue_names],
                name=args.name,
                log_job_description=True
            )
            
            # Set up signal handlers
            setup_signal_handlers(worker)
            
            # Start worker
            logger.info(f"Worker {worker.name} starting in {'burst' if args.burst else 'continuous'} mode")
            worker.work(burst=args.burst)
            
            if not args.burst:
                # If we got here in continuous mode, something went wrong
                logger.error("Worker exited unexpectedly")
                return 1
            
            logger.info("Worker completed all jobs (burst mode)")
            return 0
    
    except Exception as e:
        logger.error(f"Worker error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())