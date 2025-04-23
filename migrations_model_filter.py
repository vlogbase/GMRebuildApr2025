"""
Migration script to add UserModelFilter table to the database.
This script will create the user_model_filter table if it doesn't exist.
"""

from app import app, db
import logging

logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to add the UserModelFilter table."""
    from models import UserModelFilter
    
    logger.info("Starting migration to add UserModelFilter table")
    
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            logger.info("Migration successful: Added UserModelFilter table")
            
            # Verify the table exists
            from sqlalchemy import text
            result = db.session.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_model_filter')")).scalar()
            if result:
                logger.info("Verification successful: user_model_filter table exists")
                return True
            else:
                logger.error("Verification failed: user_model_filter table does not exist after migration")
                return False
            
        except Exception as e:
            logger.exception(f"Error during migration: {e}")
            return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Run the migration
    success = run_migration()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed. See logs for details.")