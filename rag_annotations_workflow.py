"""
Simple script to run the Flask application with RAG annotations support.
This workflow includes:
1. Running the annotations migration
2. Starting the Flask app with annotations support for context persistence
"""
import os
import sys
import logging
import time
from migrations_annotations import run_migrations

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with context persistence through annotations.
    """
    try:
        # First run the annotations migration
        logger.info("Running annotations migration...")
        if not run_migrations():
            logger.error("Failed to run annotations migration. Continuing anyway...")
        
        # Set required environment variables
        os.environ["FLASK_APP"] = "app.py"
        os.environ["FLASK_DEBUG"] = "1"
        
        # Import the Flask app
        from app import app
        
        # Run the Flask application
        logger.info("Starting Flask application with context persistence through annotations...")
        app.run(host="0.0.0.0", port=5000, debug=True)
        
    except ImportError as e:
        logger.error(f"Failed to import Flask app: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running Flask application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()