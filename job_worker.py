"""
Job Worker for GloriaMundo Chatbot

This module manages the RQ worker processes for background job execution.
"""

import os
import sys
import time
import signal
import logging
import platform
import socket
from multiprocessing import Process
from rq import Worker
from redis import Redis
from worker import create_worker

logger = logging.getLogger(__name__)

def run(queues=None, num_workers=None, worker_ttl=420, worker_name_prefix=None):
    """
    Run the job worker process
    
    Args:
        queues (list, optional): List of queue names to monitor. Defaults to all queues.
        num_workers (int, optional): Number of worker processes to start. 
                                    Defaults to number of CPU cores.
        worker_ttl (int, optional): How long (in seconds) workers should run before 
                                   restarting themselves. Defaults to 420 (7 minutes).
        worker_name_prefix (str, optional): Prefix for worker names. Defaults to hostname.
        
    Returns:
        None
    """
    # Configure logging if not already configured
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('job_worker.log')
            ]
        )
    
    # Determine number of workers based on CPU cores if not specified
    if num_workers is None:
        import multiprocessing
        num_workers = max(1, multiprocessing.cpu_count() - 1)
    
    # Generate worker name prefix if not provided
    if worker_name_prefix is None:
        worker_name_prefix = socket.gethostname()
    
    logger.info(f"Starting {num_workers} job worker(s) for queues: {queues or 'all'}")
    
    # Create and start worker processes
    processes = []
    for i in range(num_workers):
        worker_name = f"{worker_name_prefix}.worker{i+1}"
        process = Process(
            target=start_worker,
            args=(queues, worker_name, worker_ttl),
            name=worker_name
        )
        process.daemon = True
        process.start()
        processes.append(process)
        logger.info(f"Started worker process: {worker_name} (PID: {process.pid})")
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal, terminating worker processes...")
        for p in processes:
            if p.is_alive():
                logger.info(f"Terminating worker process: {p.name} (PID: {p.pid})")
                p.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Monitor worker processes and restart them if they die
    try:
        while True:
            for i, process in enumerate(processes):
                if not process.is_alive():
                    worker_name = f"{worker_name_prefix}.worker{i+1}"
                    logger.warning(f"Worker process {worker_name} (PID: {process.pid}) died, restarting...")
                    
                    # Create and start a new worker process
                    new_process = Process(
                        target=start_worker,
                        args=(queues, worker_name, worker_ttl),
                        name=worker_name
                    )
                    new_process.daemon = True
                    new_process.start()
                    
                    # Replace the dead process in our list
                    processes[i] = new_process
                    logger.info(f"Restarted worker process: {worker_name} (PID: {new_process.pid})")
                    
            time.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        for p in processes:
            if p.is_alive():
                p.terminate()
        sys.exit(0)

def start_worker(queues, name, ttl):
    """
    Start a single worker process
    
    Args:
        queues (list): List of queue names to monitor
        name (str): Worker name
        ttl (int): Time-to-live in seconds
    """
    try:
        # Create a worker using the worker factory
        worker = create_worker(queues=queues, name=name)
        
        # Set a TTL for the worker (handled by the workflow configuration)
        # Worker TTL is now managed by the workflow restart policy
        
        # Start the worker with proper exception handling
        logger.info(f"Worker {name} starting to monitor queues: {queues or 'all'}")
        worker.work()
        
    except Exception as e:
        logger.error(f"Worker {name} failed with error: {str(e)}")
        sys.exit(1)

class WorkerTTL(Exception):
    """
    Exception raised when a worker reaches its time-to-live limit.
    This allows workers to gracefully exit after a period of time,
    preventing memory leaks and other issues with long-running processes.
    """
    pass

if __name__ == "__main__":
    # Parse command line arguments if running directly
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Redis Queue workers for the GloriaMundo Chatbot")
    parser.add_argument('--queues', nargs='+', help='Queues to monitor (space-separated)')
    parser.add_argument('--workers', type=int, help='Number of worker processes to start')
    parser.add_argument('--ttl', type=int, default=420, help='Worker time-to-live in seconds')
    
    args = parser.parse_args()
    
    # Run with parsed arguments
    run(queues=args.queues, num_workers=args.workers, worker_ttl=args.ttl)