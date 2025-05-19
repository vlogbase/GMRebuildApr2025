"""
Script to run the job worker process directly without needing workflow configuration.

This script starts the background job processing system for handling asynchronous tasks.
"""

import os
import sys
import signal
import logging
import time
from job_worker_workflow import run

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('job_worker_direct.log')
    ]
)

logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """Handle termination signals gracefully"""
    logger.info("Received signal to terminate. Shutting down job worker...")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Log startup
        logger.info("Starting job worker process directly...")
        
        # Configure workers - 2 workers for stability
        os.environ['WORKER_COUNT'] = "2"
        
        # Run the job worker
        run()
    except KeyboardInterrupt:
        logger.info("Job worker process interrupted by user.")
    except Exception as e:
        logger.exception(f"Error starting job worker: {e}")
        sys.exit(1)