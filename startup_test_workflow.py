"""
Startup Performance Test Workflow

This script runs as a Replit workflow to test the startup performance
of our application with the optimized initialization system.
"""

import time
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting startup performance test workflow")
    
    # Measure app startup time
    start_time = time.time()
    logger.info("Importing application modules...")
    
    # Import app modules - this triggers all initialization
    try:
        # First import the startup cache to ensure it's available
        import startup_cache
        logger.info("Startup cache imported successfully")
        
        # Import the background initializer
        import background_initializer
        logger.info("Background initializer imported successfully")
        
        # Import app initialization module
        import app_initialization
        logger.info("App initialization module imported successfully")
        
        # Finally import the main app
        import app
        logger.info("Main app imported successfully")
        
        # Record import time
        import_time = time.time() - start_time
        logger.info(f"App imported in {import_time:.2f} seconds")
        
        # Check initialization status
        time.sleep(2)  # Wait briefly for initialization to progress
        
        if hasattr(app.app, 'config') and 'BACKGROUND_INITIALIZER' in app.app.config:
            initializer = app.app.config['BACKGROUND_INITIALIZER']
            
            # Monitor initialization progress
            max_wait = 30  # seconds
            check_interval = 0.5  # seconds
            start_wait = time.time()
            
            logger.info(f"Monitoring background initialization for up to {max_wait} seconds")
            
            last_completed = 0
            total_tasks = len(initializer.tasks) if hasattr(initializer, 'tasks') else 0
            
            while time.time() - start_wait < max_wait and not initializer.all_completed():
                time.sleep(check_interval)
                
                # Get current status
                completed = len(initializer.results) if hasattr(initializer, 'results') else 0
                
                # Print progress if changed
                if completed != last_completed:
                    logger.info(f"Completed {completed}/{total_tasks} initialization tasks")
                    last_completed = completed
            
            # Final status
            status = initializer.get_status_summary()
            logger.info("Initialization complete:")
            logger.info(f" - Tasks total: {status['tasks_total']}")
            logger.info(f" - Tasks completed: {status['tasks_completed']}")
            logger.info(f" - Tasks successful: {status['tasks_successful']}")
            logger.info(f" - Tasks failed: {status['tasks_failed']}")
            
            if status['tasks_failed'] > 0:
                logger.warning("Some initialization tasks failed:")
                for name, details in status['task_details'].items():
                    if details['status'] == 'failed':
                        logger.warning(f" - Failed task: {name}, Error: {details.get('error', 'Unknown')}")
        else:
            logger.warning("Background initializer not found in app configuration")
        
        # Check Azure storage initialization
        if hasattr(app, 'USE_AZURE_STORAGE'):
            logger.info(f"Azure Storage initialized: {app.USE_AZURE_STORAGE}")
        
        # Get overall timing
        total_time = time.time() - start_time
        logger.info(f"Total startup test time: {total_time:.2f} seconds")
        
        # Summary report
        logger.info("=== STARTUP PERFORMANCE SUMMARY ===")
        logger.info(f"Import time: {import_time:.2f}s")
        logger.info(f"Total startup time: {total_time:.2f}s")
        logger.info("=================================")
        
    except Exception as e:
        logger.error(f"Error during startup test: {e}", exc_info=True)
        sys.exit(1)
        
    logger.info("Startup performance test workflow completed successfully")
    sys.exit(0)