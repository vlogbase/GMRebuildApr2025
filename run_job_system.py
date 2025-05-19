"""
Complete Job System Runner

This script starts both the main application and the background job worker process
in separate threads to provide a complete working system in a single command.
"""

import os
import sys
import time
import signal
import threading
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('job_system.log')
    ]
)

logger = logging.getLogger(__name__)

# Global flag to track if we're shutting down
shutting_down = False

def signal_handler(sig, frame):
    """Handle termination signals gracefully"""
    global shutting_down
    logger.info("Received signal to terminate. Shutting down job system...")
    shutting_down = True
    sys.exit(0)

def run_app_server():
    """Run the main application server"""
    try:
        logger.info("Starting application server...")
        # Use subprocess to run the app with proper environment isolation
        process = subprocess.Popen(
            ["python", "app_workflow.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Stream logs in real-time
        for line in process.stdout:
            logger.info(f"[APP] {line.strip()}")
            
            # Check if we're shutting down
            if shutting_down:
                process.terminate()
                break
                
        # Wait for process to complete
        process.wait()
        logger.info(f"Application server exited with code: {process.returncode}")
        
    except Exception as e:
        logger.exception(f"Error running application server: {e}")

def run_job_worker():
    """Run the job worker process"""
    try:
        logger.info("Starting job worker...")
        # Use subprocess to run the worker with proper environment isolation
        process = subprocess.Popen(
            ["python", "job_worker_workflow.py", "--workers", "2"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Stream logs in real-time
        for line in process.stdout:
            logger.info(f"[WORKER] {line.strip()}")
            
            # Check if we're shutting down
            if shutting_down:
                process.terminate()
                break
                
        # Wait for process to complete
        process.wait()
        logger.info(f"Job worker exited with code: {process.returncode}")
        
    except Exception as e:
        logger.exception(f"Error running job worker: {e}")

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create threads for app server and job worker
        app_thread = threading.Thread(target=run_app_server)
        worker_thread = threading.Thread(target=run_job_worker)
        
        # Set threads as daemon so they exit when main thread exits
        app_thread.daemon = True
        worker_thread.daemon = True
        
        # Start the threads
        logger.info("Starting job system (app server + job worker)...")
        app_thread.start()
        
        # Small delay to ensure app starts first
        time.sleep(2)
        
        worker_thread.start()
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
            # Exit if any thread has died
            if not app_thread.is_alive() or not worker_thread.is_alive():
                logger.warning("A component has stopped running - shutting down job system")
                break
                
    except KeyboardInterrupt:
        logger.info("Job system interrupted by user")
    except Exception as e:
        logger.exception(f"Error starting job system: {e}")
    finally:
        # Set the shutdown flag
        shutting_down = True
        logger.info("Job system shutdown complete")