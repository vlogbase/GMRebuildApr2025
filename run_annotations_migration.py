"""
Script to run the annotations migration to add the annotations column to the Message table.
This is needed for context persistence with OpenRouter annotations.
"""
import sys
import logging
from migrations_annotations import run_migrations

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Running annotations migration...")
    
    if run_migrations():
        logger.info("Annotations migration completed successfully.")
        sys.exit(0)
    else:
        logger.error("Annotations migration failed.")
        sys.exit(1)