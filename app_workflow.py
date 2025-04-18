"""
Simple script to run the Flask application for testing in the Replit environment.
"""
import os
import logging
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run the Flask application using gunicorn with gevent workers."""
    try:
        logger.info("Starting the Flask application...")
        
        # Command to run with gunicorn
        cmd = [
            "gunicorn",
            "main:app",
            "-k", "gevent",  # Use gevent worker
            "-w", "4",       # 4 worker processes
            "--timeout", "300",  # 5 minute timeout
            "--bind", "0.0.0.0:5000",  # Bind to all interfaces
            "--reload"       # Auto-reload on file changes
        ]
        
        # Run the process
        logger.info(f"Running command: {' '.join(cmd)}")
        process = subprocess.run(cmd)
        
        # Check if process ran successfully
        if process.returncode != 0:
            logger.error(f"Process exited with code {process.returncode}")
            return process.returncode
        
        return 0
    except Exception as e:
        logger.exception(f"Error running application: {e}")
        return 1

if __name__ == "__main__":
    main()