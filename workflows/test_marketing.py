"""
Simple Flask server workflow for testing the marketing page at /info
"""
import sys
import os
import subprocess
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with the marketing page
    """
    try:
        logger.info("Starting Flask server for marketing page testing")
        
        # Get the Flask app path
        app_path = os.path.join(os.getcwd(), 'app.py')
        
        # Run the Flask application
        logger.info(f"Running Flask application from {app_path}")
        process = subprocess.Popen(
            [sys.executable, app_path],
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info("Flask server started for testing the marketing page")
        logger.info("Visit http://localhost:5000/info to see the marketing page")
        
        # Keep the server running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        if process and process.poll() is None:
            process.terminate()
            process.wait()
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        if process and process.poll() is None:
            process.terminate()
            process.wait()

if __name__ == "__main__":
    run()