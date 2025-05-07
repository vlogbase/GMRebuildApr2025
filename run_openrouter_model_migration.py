#!/usr/bin/env python3
"""
Script to run OpenRouter model database migrations.
This script separates the schema migration from data population.
The schema migration is run first, and then the application
will handle populating the data when it starts.
"""

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migrations():
    """Run OpenRouter model database migrations"""
    try:
        from migrations_openrouter_model import run_migrations
        logger.info("Starting OpenRouter model migrations...")
        success = run_migrations()
        
        if success:
            logger.info("OpenRouter model migrations completed successfully")
        else:
            logger.warning("OpenRouter model migrations had issues")
            
        return success
    except Exception as e:
        logger.error(f"Error running OpenRouter model migrations: {e}")
        return False

if __name__ == "__main__":
    run_migrations()