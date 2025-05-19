#!/usr/bin/env python
"""
Start Job Worker

This script starts a job worker process to process background jobs from Redis queues.
It's designed to be run from the command line and can be configured with arguments.
"""

import os
import sys
import argparse
import logging
import subprocess
import threading
import time
import signal
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Start Redis Queue job worker")
    
    parser.add_argument('--queues', help='Comma-separated list of queue names to work on')
    parser.add_argument('--name', help='Worker name (default: hostname:pid)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    parser.add_argument('--burst', action='store_true', help='Run in burst mode (quit after all work is done)')
    parser.add_argument('--worker-count', type=int, default=1, help='Number of worker processes to start')
    parser.add_argument('--workflow', action='store_true', help='Start worker in Replit workflow')
    
    return parser.parse_args()

def start_worker_process(queues=None, name=None, log_level='INFO', burst=False, workflow=False):
    """
    Start a worker process
    
    Args:
        queues (list): List of queue names
        name (str): Worker name
        log_level (str): Logging level
        burst (bool): Run in burst mode
        workflow (bool): Start worker in Replit workflow
        
    Returns:
        subprocess.Popen: The worker process
    """
    if queues is None:
        queues = ['high', 'default', 'low', 'email', 'indexing']
    
    if isinstance(queues, list):
        queues_str = ','.join(queues)
    else:
        queues_str = queues
    
    env = os.environ.copy()
    
    if workflow:
        # Start worker in Replit workflow
        cmd = [
            'python', 'job_worker_workflow.py'
        ]
        
        # Set environment variables for the workflow
        env['WORKER_ARGS'] = f'--queues {queues_str}'
        if name:
            env['WORKER_ARGS'] += f' --name {name}'
        env['WORKER_ARGS'] += f' --log-level {log_level}'
        
        logger.info(f"Starting job worker in Replit workflow with queues: {queues_str}")
        
        # Return immediately, don't start a process (will be handled by the workflow)
        return None
    else:
        # Start worker directly
        cmd = [
            'python', 'job_worker.py'
        ]
        
        # Add command line arguments
        if queues_str:
            cmd.extend(queues_str.split(','))
        if name:
            cmd.extend(['--name', name])
        if burst:
            cmd.append('--burst')
        cmd.extend(['--log-level', log_level])
        
        logger.info(f"Starting job worker process with command: {' '.join(cmd)}")
        
        # Start the process
        return subprocess.Popen(cmd, env=env)

def monitor_workers(workers, stop_event):
    """
    Monitor worker processes and restart them if they die
    
    Args:
        workers (list): List of worker processes
        stop_event (threading.Event): Event to signal shutdown
    """
    logger.info("Worker monitor thread started")
    
    while not stop_event.is_set():
        # Check each worker
        for i, worker in enumerate(workers):
            if worker is not None and worker.poll() is not None:
                # Worker has died, restart it
                logger.warning(f"Worker process {i+1} died, restarting...")
                workers[i] = start_worker_process()
        
        # Sleep for a bit
        time.sleep(5)
    
    logger.info("Worker monitor thread stopped")

def main():
    """Main entry point"""
    args = parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Parse queues
    queues = args.queues.split(',') if args.queues else None
    
    if args.workflow:
        # Start worker in Replit workflow - this doesn't actually start a process here,
        # it just sets up environment variables that will be used by the workflow script
        start_worker_process(
            queues=queues,
            name=args.name,
            log_level=args.log_level,
            burst=args.burst,
            workflow=True
        )
        
        # Print instructions
        logger.info("Job worker environment configured for Replit workflow")
        logger.info("Start the workflow with: 'replit workflow run job_worker'")
        
        return 0
    
    # Start worker processes
    workers = []
    for i in range(args.worker_count):
        # Generate a unique name for each worker
        worker_name = args.name
        if worker_name and args.worker_count > 1:
            worker_name = f"{worker_name}-{i+1}"
        
        # Start the worker
        worker = start_worker_process(
            queues=queues,
            name=worker_name,
            log_level=args.log_level,
            burst=args.burst
        )
        
        if worker:
            workers.append(worker)
    
    if not workers:
        logger.error("Failed to start any worker processes")
        return 1
    
    # Set up signal handlers for graceful shutdown
    stop_event = threading.Event()
    
    def handle_signal(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        stop_event.set()
        
        # Terminate all worker processes
        for worker in workers:
            if worker:
                worker.terminate()
        
        # Exit main process
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Start monitor thread to restart workers if they die
    if not args.burst:
        monitor_thread = threading.Thread(target=monitor_workers, args=(workers, stop_event))
        monitor_thread.daemon = True
        monitor_thread.start()
    
    # Wait for all workers to complete (only relevant for burst mode)
    for worker in workers:
        worker.wait()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())