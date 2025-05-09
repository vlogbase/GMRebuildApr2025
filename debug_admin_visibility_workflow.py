"""
Debug workflow for testing admin tab visibility.
This workflow simulates the admin dashboard access with a focus on tab visibility.
"""
import os
import logging
import sys
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('admin_visibility_test.log')
    ]
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the debug admin visibility test.
    This provides a controlled environment to test the admin tab visibility issues.
    """
    try:
        logger.info("Starting admin tab visibility test workflow...")
        
        # Set admin emails
        admin_emails = "test@example.com,andy@sentigral.com,admin@example.com"
        os.environ['ADMIN_EMAILS'] = admin_emails
        logger.info(f"Admin emails set to: {admin_emails}")
        
        # Set session secret
        os.environ['SESSION_SECRET'] = 'debug_session_secret_for_testing'
        
        # Log script information
        logger.info("Starting debug_admin_visibility.py with Python...")
        
        # Run the debug script as a subprocess
        process = subprocess.Popen(
            ['python', 'debug_admin_visibility.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Log output in real-time
        for line in process.stdout:
            logger.info(f"App: {line.strip()}")
        
        # Log errors
        for line in process.stderr:
            logger.error(f"Error: {line.strip()}")
        
        # Wait for process to complete
        return_code = process.wait()
        logger.info(f"Debug script exited with code {return_code}")
        
        if return_code != 0:
            logger.error("Debug script failed - check logs for details")
            sys.exit(return_code)
            
    except Exception as e:
        logger.error(f"Error running admin tab test: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run()