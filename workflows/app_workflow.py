"""
Application workflow for GloriaMundo

This script starts the application server using the correct gunicorn configuration
with gevent worker class for optimal performance.
"""
import logging
import os
import sys

def main():
    """Main function to start the application server"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting GloriaMundo application server...")
    
    # Set the correct working directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Configure Gunicorn command
    bind_address = "0.0.0.0:5000"  # Bind to all interfaces on port 5000
    workers = 1  # Use 1 worker for simplicity in development
    worker_class = "gevent"  # Use gevent for async support
    timeout = 120  # Increase timeout for long-running requests
    
    # Build the Gunicorn command
    cmd = [
        "gunicorn",
        f"--bind={bind_address}",
        f"--workers={workers}",
        f"--worker-class={worker_class}",
        f"--timeout={timeout}",
        "main:app"  # Use main.py's app as the WSGI entry point
    ]
    
    # Print command for debugging
    logger.info(f"Running command: {' '.join(cmd)}")
    
    # Execute Gunicorn
    try:
        os.execvp(cmd[0], cmd)
    except Exception as e:
        logger.error(f"Failed to start application server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()