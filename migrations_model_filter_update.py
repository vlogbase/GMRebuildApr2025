"""
Migration script to update UserModelFilter default values to 1500.0.
This script will update any existing filter settings to the new maximum.
"""

from app import app, db
import logging

logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to update UserModelFilter default values."""
    from models import UserModelFilter
    
    logger.info("Starting migration to update UserModelFilter default values")
    
    with app.app_context():
        try:
            # Update existing records where max costs are below the new maximum
            logger.info("Updating existing UserModelFilter records with new default values")
            from sqlalchemy import text
            
            # Verify the table exists
            table_exists = db.session.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_model_filter')")).scalar()
            if not table_exists:
                logger.error("user_model_filter table does not exist")
                return False
            
            # Update records
            result = db.session.execute(text("""
                UPDATE user_model_filter
                SET max_input_cost = 1500.0, max_output_cost = 1500.0
                WHERE max_input_cost < 1500.0 OR max_output_cost < 1500.0
            """))
            db.session.commit()
            
            updated_count = result.rowcount
            logger.info(f"Updated {updated_count} UserModelFilter records")
            
            return True
            
        except Exception as e:
            logger.exception(f"Error during migration: {e}")
            db.session.rollback()
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