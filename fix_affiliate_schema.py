"""
Fix the Affiliate model to include a user_id field.

This script:
1. Adds a user_id field to the Affiliate model if it doesn't exist
2. Creates a migration to update existing affiliates with their corresponding user_id based on email matching
"""

import logging
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, inspect
from app import app, db
from models import Affiliate, User

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_if_user_id_exists():
    """Check if user_id column already exists in the Affiliate table"""
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('affiliate')]
    return 'user_id' in columns

def add_user_id_field():
    """Add user_id field to Affiliate model if it doesn't exist"""
    if check_if_user_id_exists():
        logger.info("user_id field already exists in Affiliate table")
        return False
    
    try:
        # Add the column to the database
        logger.info("Adding user_id column to Affiliate table")
        db.engine.execute('ALTER TABLE affiliate ADD COLUMN user_id INTEGER REFERENCES user(id)')
        
        # Update existing records to set user_id based on email matching
        logger.info("Updating existing affiliate records with user_id")
        with db.session.begin():
            affiliates = Affiliate.query.all()
            updated_count = 0
            
            for affiliate in affiliates:
                # Find user with matching email
                user = User.query.filter_by(email=affiliate.email).first()
                if user:
                    db.engine.execute(
                        'UPDATE affiliate SET user_id = %s WHERE id = %s',
                        (user.id, affiliate.id)
                    )
                    updated_count += 1
            
            logger.info(f"Updated {updated_count} affiliate records with user_id")
        
        logger.info("Successfully added and populated user_id field in Affiliate table")
        return True
    except Exception as e:
        logger.error(f"Error adding user_id field: {str(e)}")
        return False

def run_migration():
    """Run the migration to add user_id field to Affiliate model"""
    with app.app_context():
        if add_user_id_field():
            logger.info("Migration completed successfully")
        else:
            logger.info("Migration not needed or failed")

if __name__ == "__main__":
    run_migration()