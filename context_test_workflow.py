"""
Simple workflow to test the app context fixes by running test_app_context.py
"""

import logging
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('context_test.log')
    ]
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the app context test and display the results
    """
    logger.info("Starting app context test workflow")
    
    try:
        # Run the test script
        logger.info("Running test_app_context.py...")
        result = subprocess.run(
            [sys.executable, "test_app_context.py"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Log the results
        logger.info("Test completed successfully")
        logger.info("STDOUT:")
        for line in result.stdout.split('\n'):
            if line.strip():
                logger.info(f"  {line}")
        
        # Check for errors
        if result.stderr:
            logger.warning("STDERR (there were warnings or errors):")
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.warning(f"  {line}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Test failed with return code {e.returncode}")
        logger.error("STDOUT:")
        for line in e.stdout.split('\n'):
            if line.strip():
                logger.info(f"  {line}")
        
        logger.error("STDERR:")
        for line in e.stderr.split('\n'):
            if line.strip():
                logger.error(f"  {line}")
    except Exception as e:
        logger.error(f"Error running test: {e}")
    
    logger.info("App context test workflow completed. Check context_test.log for details.")

if __name__ == "__main__":
    run()