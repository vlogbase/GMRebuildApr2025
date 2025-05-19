#!/usr/bin/env python
"""
Start Job Worker

This script starts a RQ worker for processing background jobs.
It's designed to be run as a separate process from the main Flask application.

Usage:
    python start_job_worker.py [queue_names]

Arguments:
    queue_names: Optional space-separated list of queue names to listen to
                Default: 'high default low'
"""

import os
import sys
import logging
import time
import signal
import argparse
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('job_worker.log')
    ]
)
logger = logging.getLogger('job_worker')

# Import job worker module
from job_worker import run_worker

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Start Redis Queue worker for background jobs')
    parser.add_argument(
        'queue_names',
        nargs='*',
        default=['high', 'default', 'low'],
        help='Queue names to listen to (default: high default low)'
    )
    parser.add_argument(
        '--burst',
        action='store_true',
        help='Run in burst mode (process existing jobs and exit)'
    )
    parser.add_argument(
        '--name',
        type=str,
        default=None,
        help='Worker name (default: hostname:pid:queues)'
    )
    parser.add_argument(
        '--worker-ttl',
        type=int,
        default=420,
        help='Worker timeout in seconds (default: 420)'
    )
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Log startup
    logger.info(f"Starting job worker on queues: {', '.join(args.queue_names)}")
    logger.info(f"Burst mode: {args.burst}")
    if args.name:
        logger.info(f"Worker name: {args.name}")
    
    # Set up signal handling for graceful shutdown
    def handle_signal(signum, frame):
        logger.info(f"Received signal {signum}, initiating worker shutdown")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    try:
        # Run the worker
        exit_code = run_worker(
            queue_names=args.queue_names,
            burst=args.burst,
            name=args.name,
            worker_ttl=args.worker_ttl
        )
        
        # Log exit
        logger.info(f"Worker exited with code {exit_code}")
        return exit_code
    
    except Exception as e:
        logger.error(f"Error running worker: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())