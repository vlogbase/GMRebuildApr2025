"""
Simple Benchmark Script for Startup Performance

This script measures the basic app import time to verify optimization improvements.
"""

import time
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def main():
    """Run a simple benchmark of app import time"""
    logger.info("Starting benchmark")
    
    # Measure startup time
    start_time = time.time()
    
    # Import app - this triggers initialization
    logger.info("Importing app module...")
    import app
    
    # Calculate import time
    import_time = time.time() - start_time
    logger.info(f"App imported in {import_time:.2f} seconds")
    
    # Check Azure Storage status
    if hasattr(app, 'USE_AZURE_STORAGE'):
        logger.info(f"Azure Storage status: {app.USE_AZURE_STORAGE}")
    
    # Check if we're using the background initializer
    if hasattr(app.app, 'config') and 'BACKGROUND_INITIALIZER' in app.app.config:
        logger.info("Using background initializer: Yes")
    else:
        logger.info("Using background initializer: No")
    
    # Log performance metrics
    logger.info("===== PERFORMANCE METRICS =====")
    logger.info(f"App import time: {import_time:.2f}s")
    logger.info("==============================")
    
    return import_time

if __name__ == "__main__":
    main()