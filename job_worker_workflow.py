"""
Redis Queue Worker for GloriaMundo Chatbot

This script runs the RQ worker process that executes background jobs.
It's configured to run as a Replit workflow separate from the main application.
"""

import os
import sys
import time
import signal
import logging
import argparse
from redis import Redis
from redis.exceptions import ConnectionError, TimeoutError
from rq import Worker
from job_worker import run as run_worker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('job_worker_workflow.log')
    ]
)

logger = logging.getLogger(__name__)

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown"""
    def handle_shutdown_signal(signum, frame):
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)

def test_redis_connection():
    """Test the Redis connection and wait for it to be available"""
    from redis_cache import redis_cache
    
    max_retries = 5
    retry_count = 0
    retry_delay = 2
    
    while retry_count < max_retries:
        try:
            redis = redis_cache.get_redis()
            redis.ping()
            logger.info("Redis connection successful")
            return True
        except (ConnectionError, TimeoutError) as e:
            retry_count += 1
            logger.warning(f"Redis connection failed (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 1.5  # Exponential backoff
            else:
                logger.error("Failed to connect to Redis after multiple attempts. Exiting.")
                return False
        except Exception as e:
            logger.exception(f"Unexpected error connecting to Redis: {e}")
            return False

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run RQ Worker')
    parser.add_argument('--queues', type=str, nargs='*',
                        help='Queues to monitor (default: all queues)')
    parser.add_argument('--workers', type=int, default=None,
                        help='Number of worker processes to start')
    parser.add_argument('--ttl', type=int, default=420,
                        help='Worker time-to-live in seconds (default: 420)')
    
    return parser.parse_args()

def run():
    """Run the job worker process"""
    args = parse_arguments()
    
    # Set up signal handlers for graceful shutdown
    setup_signal_handlers()
    
    logger.info("Starting GloriaMundo Job Worker...")
    
    # Test Redis connection before starting workers
    if not test_redis_connection():
        sys.exit(1)
    
    try:
        # Run the worker(s)
        run_worker(
            queues=args.queues,
            num_workers=args.workers,
            worker_ttl=args.ttl
        )
    except Exception as e:
        logger.exception(f"Error running worker: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()