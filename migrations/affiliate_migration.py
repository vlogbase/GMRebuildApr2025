"""
Migration script to add user_id to affiliate table and update existing records
"""

import logging
from datetime import datetime
from sqlalchemy import inspect
from sqlalchemy.sql import text

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migration(app, db):
    """Run the migration to add user_id field to affiliate table and link existing records"""
    logger.info("Starting affiliate user_id migration...")
    
    with app.app_context():
        try:
            # Check if user_id column already exists
            inspector = inspect(db.engine)
            columns = [c['name'] for c in inspector.get_columns('affiliate')]
            
            # Only add the column if it doesn't exist
            if 'user_id' not in columns:
                logger.info("Adding user_id column to affiliate table")
                db.session.execute(text('ALTER TABLE affiliate ADD COLUMN user_id INTEGER REFERENCES "user"(id)'))
                db.session.commit()
                logger.info("Successfully added user_id column to affiliate table")
            else:
                logger.info("user_id column already exists in affiliate table")
            
            # Update existing affiliates with matching user_id
            from models import User, Affiliate
            
            # Get all affiliates with no user_id set
            # We need to avoid using the attribute directly since it might not exist in older code
            unlinked_affiliates = db.session.execute(
                text("SELECT id, email FROM affiliate WHERE user_id IS NULL")
            ).fetchall()
            count = 0
            
            if not unlinked_affiliates:
                logger.info("No unlinked affiliates found")
                return True
                
            logger.info(f"Found {len(unlinked_affiliates)} unlinked affiliates")
            
            for affiliate_id, affiliate_email in unlinked_affiliates:
                # Find matching user by email
                user = User.query.filter_by(email=affiliate_email).first()
                
                if user:
                    logger.info(f"Linking affiliate {affiliate_id} to user {user.id}")
                    db.session.execute(
                        text("UPDATE affiliate SET user_id = :user_id WHERE id = :affiliate_id"),
                        {"user_id": user.id, "affiliate_id": affiliate_id}
                    )
                    count += 1
                else:
                    logger.warning(f"No user found with email {affiliate_email} for affiliate {affiliate_id}")
            
            if count > 0:
                db.session.commit()
                logger.info(f"Successfully linked {count} affiliates to users")
            
            logger.info("Affiliate user_id migration completed")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in affiliate user_id migration: {e}", exc_info=True)
            return False