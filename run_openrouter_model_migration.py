#!/usr/bin/env python3
"""
Run OpenRouter Model Migration Script

This is a simple utility script to run the OpenRouter model migrations.
This adds new fields to the OpenRouterModel table and ensures data is up-to-date.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migrations():
    """Import and run the migrations from migrations_openrouter_model.py"""
    try:
        from migrations_openrouter_model import run_migrations as perform_migrations
        
        logger.info("Starting OpenRouter model migrations...")
        success = perform_migrations()
        
        if success:
            logger.info("OpenRouter model migrations completed successfully.")
            return True
        else:
            logger.error("OpenRouter model migrations failed.")
            return False
            
    except ImportError as e:
        logger.error(f"Failed to import migrations_openrouter_model: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running migrations: {e}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)