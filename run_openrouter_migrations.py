#!/usr/bin/env python3
"""
Run OpenRouter migrations utility script

This script runs the OpenRouter model migrations to ensure the database
is updated with the latest model data.
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        from migrations_openrouter_model import run_migrations
        
        logger.info("Running OpenRouter model migrations...")
        success = run_migrations()
        
        if success:
            logger.info("OpenRouter model migrations completed successfully")
            return 0
        else:
            logger.error("OpenRouter model migrations failed")
            return 1
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)