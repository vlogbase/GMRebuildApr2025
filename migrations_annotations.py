"""
Migration script to add annotations column to Message table
This supports OpenRouter's context persistence feature via annotations.
"""
import os
import logging
import sys
from sqlalchemy import create_engine, text as sa_text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migrations():
    """
    Run migrations to add annotations column to Message table.
    This function:
    1. Adds a JSON annotations column to the Message model
    2. Ensures the column has appropriate constraints and defaults
    """
    try:
        # Get database URL from environment
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            sys.exit(1)
            
        # Create engine
        engine = create_engine(db_url)
        
        # Run migrations within a transaction
        with engine.connect() as conn:
            conn.execute(sa_text("BEGIN"))
            try:
                # Check if annotations column exists
                result = conn.execute(sa_text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'message' AND column_name = 'annotations'"
                ))
                
                if not result.fetchone():
                    logger.info("Adding annotations column to message table")
                    # Use JSONB for better performance and indexing in PostgreSQL
                    conn.execute(sa_text(
                        "ALTER TABLE message ADD COLUMN annotations JSONB"
                    ))
                    logger.info("annotations column added successfully")
                else:
                    logger.info("annotations column already exists in message table")
                    
                conn.execute(sa_text("COMMIT"))
                logger.info("Migrations completed successfully")
                
            except Exception as e:
                conn.execute(sa_text("ROLLBACK"))
                logger.error(f"Error during migrations, rolling back: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        return False
        
    return True

if __name__ == "__main__":
    logger.info("Starting migrations for annotations column")
    if run_migrations():
        logger.info("Migrations completed successfully")
        sys.exit(0)
    else:
        logger.error("Migrations failed")
        sys.exit(1)