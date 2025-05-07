#!/usr/bin/env python3
"""
Run the OpenRouter model database migrations.

This script is intended to be run from the command line to create and 
populate the OpenRouterModel table in the database.
"""

import logging
import sys
from migrations_openrouter_model import run_migrations

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Running OpenRouter model database migrations...")
    success = run_migrations()
    
    if success:
        logger.info("OpenRouter model database migrations completed successfully")
        sys.exit(0)
    else:
        logger.error("OpenRouter model database migrations failed")
        sys.exit(1)