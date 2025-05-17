"""
Startup Performance Test Script

This script measures the application startup time with the optimized initialization system
and generates a report on performance improvements.
"""

import time
import logging
import threading
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the startup performance test"""
    logger.info("Starting startup performance test")
    
    # Record the start time
    start_time = time.time()
    
    # Import the Flask app - this triggers all initialization
    logger.info("Importing Flask app...")
    import app
    
    # Record the import time
    import_time = time.time() - start_time
    logger.info(f"App imported in {import_time:.2f} seconds")
    
    # Check for background initializer
    if hasattr(app.app, 'config') and 'BACKGROUND_INITIALIZER' in app.app.config:
        logger.info("Background initializer found in app config")
        initializer = app.app.config['BACKGROUND_INITIALIZER']
        
        # Wait for all initialization tasks to complete with a timeout
        max_wait_time = 30  # seconds
        wait_start = time.time()
        
        logger.info(f"Waiting up to {max_wait_time}s for all background tasks to complete...")
        while not initializer.all_completed() and (time.time() - wait_start) < max_wait_time:
            time.sleep(0.5)
            
        # Get final status
        total_time = time.time() - start_time
        
        # Check if all tasks completed or timeout occurred
        if initializer.all_completed():
            logger.info(f"All background tasks completed in {total_time:.2f} seconds")
        else:
            logger.warning(f"Hit timeout after {max_wait_time}s waiting for background tasks")
            
        # Get details about initialization tasks
        status = initializer.get_status_summary()
        
        logger.info(f"Completed {status['tasks_completed']}/{status['tasks_total']} tasks")
        logger.info(f"Tasks successful: {status['tasks_successful']}")
        logger.info(f"Tasks failed: {status['tasks_failed']}")
        logger.info(f"Tasks pending: {status['tasks_pending']}")
        
        # Log details for each task
        logger.info("Task details:")
        for name, details in status['task_details'].items():
            status_str = details['status']
            time_str = f"{details['time_taken']:.2f}s" if details['time_taken'] is not None else "N/A"
            logger.info(f"  - {name}: {status_str} ({time_str})")
            
            # Log errors for failed tasks
            if details['error']:
                logger.error(f"    Error: {details['error']}")
    else:
        logger.warning("Background initializer not found in app config")
        total_time = time.time() - start_time
        
    logger.info(f"Total startup test time: {total_time:.2f} seconds")
    logger.info("Startup performance test completed")
    
    # Check Azure Storage initialization
    if hasattr(app, 'USE_AZURE_STORAGE'):
        logger.info(f"Azure Storage initialization status: {app.USE_AZURE_STORAGE}")
    
    return {
        'import_time': import_time,
        'total_time': total_time,
    }

if __name__ == "__main__":
    main()