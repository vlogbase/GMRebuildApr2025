#!/usr/bin/env python3
"""
Start the application with the database migration included.
This script runs the OpenRouter model migrations and then starts the Flask app.
"""

import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        # First run the database migrations
        logger.info("Running OpenRouter model migrations...")
        
        try:
            from run_openrouter_model_migration import run_migrations
            success = run_migrations()
            
            if not success:
                logger.warning("OpenRouter model migrations had issues, continuing anyway...")
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            logger.warning("Continuing despite migration errors...")
        
        # Then start the Flask app
        logger.info("Starting Flask application...")
        subprocess.run(["python", "app.py"])
        
        return 0
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())