"""
Run Script for GloriaMundo Chatbot Application
This is the entry point for the Replit workflow to start the application.
"""
import os
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_migrations():
    """Run database migrations"""
    logger.info("Running database migrations...")
    try:
        # Run migrations for image_url field
        subprocess.run(["python", "migrations_image_url.py"], check=True)
        logger.info("Database migrations completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running migrations: {e}")
        # Continue anyway, as the error might be that the column already exists

def start_server():
    """Start the Flask server with Gunicorn and Gevent workers"""
    logger.info("Starting server with Gunicorn and Gevent workers...")
    
    # Build the command
    cmd = [
        "gunicorn", 
        "main:app", 
        "-k", "gevent",
        "-w", "4",
        "--timeout", "300",
        "--bind", "0.0.0.0:5000",
        "--reload"
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    # Execute the command (this replaces the current process)
    os.execvp(cmd[0], cmd)

if __name__ == "__main__":
    logger.info("Starting GloriaMundo Chatbot Application")
    
    # Run database migrations
    run_migrations()
    
    # Start the server
    start_server()