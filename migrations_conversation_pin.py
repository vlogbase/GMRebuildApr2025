"""
Migration script to add the is_pinned field to the Conversation table.
"""

import logging
from datetime import datetime
from sqlalchemy import Column, Boolean

logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to add the is_pinned field to the Conversation table."""
    try:
        from app import app, db
        from models import Conversation
        
        with app.app_context():
            logger.info("Starting migration to add is_pinned field to Conversation table")
            
            # Check if the is_pinned column already exists
            inspector = db.inspect(db.engine)
            if 'is_pinned' not in [col['name'] for col in inspector.get_columns('conversation')]:
                # Add the is_pinned column
                from sqlalchemy import text
                db.session.execute(text('ALTER TABLE conversation ADD COLUMN is_pinned BOOLEAN DEFAULT FALSE'))
                logger.info("Added is_pinned column to Conversation table")
            else:
                logger.info("is_pinned column already exists in Conversation table")
                
            # Commit the changes
            db.session.commit()
            logger.info("Migration completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"Error during migration: {e}")
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
        print("Migration failed. Check the logs for details.")