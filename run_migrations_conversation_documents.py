"""
Run the migration script for conversation documents.
"""
import os
import logging
import sys
from migrations_conversation_documents import run_migration

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('run_migrations')

def main():
    """Run the migration script and report results."""
    try:
        logger.info("Starting conversation document migration")
        success = run_migration()
        
        if success:
            logger.info("Conversation document migration completed successfully")
            return 0
        else:
            logger.error("Conversation document migration failed")
            return 1
    except Exception as e:
        logger.exception(f"Error during migration: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())