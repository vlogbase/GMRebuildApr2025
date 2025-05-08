"""
Script to run migrations for model activity status fields
"""

import logging
import sys
from migrations_model_activity import run_migrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Run migrations for model activity status fields
    """
    try:
        logger.info("Starting model activity status migrations")
        success = run_migrations()
        
        if success:
            logger.info("Model activity status migrations completed successfully")
            return 0
        else:
            logger.error("Model activity status migrations failed")
            return 1
            
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())