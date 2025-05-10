"""
Simple script to run the Flask application for testing the document visual indicator feature.
"""
import os
import sys
import subprocess
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application.
    """
    try:
        logger.info("Starting Flask application...")
        
        # Get the port from environment or use default
        port = os.environ.get('PORT', '5000')
        
        # Command to run the Flask app
        cmd = [
            sys.executable,  # Use the current Python executable
            "app.py"
        ]
        
        # Run the command and stream output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        logger.info(f"Flask application started on port {port}")
        logger.info("Press Ctrl+C to stop")
        
        # Stream the output
        for line in process.stdout:
            sys.stdout.write(line)
        
        # Wait for the process to complete
        process.wait()
        
        if process.returncode != 0:
            logger.error(f"Flask application exited with code {process.returncode}")
            return process.returncode
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Stopping Flask application...")
        return 0
    except Exception as e:
        logger.exception(f"Error running Flask application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run())