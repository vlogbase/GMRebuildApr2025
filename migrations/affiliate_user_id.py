"""
Migration to add user_id to the Affiliate model and map existing affiliates to users.

This script:
1. Checks if the user_id column exists in the affiliate table
2. Adds it if it doesn't exist
3. Updates existing affiliates with user IDs based on matching email addresses
"""

import logging
from sqlalchemy import inspect, Column, Integer, ForeignKey
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migration(app, db):
    """
    Run the migration to add user_id to Affiliate table
    
    Args:
        app: Flask application instance
        db: SQLAlchemy database instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Starting Affiliate user_id migration...")
    
    try:
        with app.app_context():
            # Import models inside app context to avoid circular imports
            from models import Affiliate, User
            
            # Check if user_id column already exists
            inspector = inspect(db.engine)
            columns = [c['name'] for c in inspector.get_columns('affiliate')]
            
            if 'user_id' in columns:
                logger.info("user_id column already exists in affiliate table")
                
                # Check if there are unlinked affiliates we need to link
                unlinked_count = db.session.execute(
                    "SELECT COUNT(*) FROM affiliate WHERE user_id IS NULL"
                ).scalar()
                
                if unlinked_count == 0:
                    logger.info("All affiliates are already linked to users")
                    return True
                
                logger.info(f"Found {unlinked_count} unlinked affiliates to update")
            else:
                # Add user_id column to affiliate table
                logger.info("Adding user_id column to affiliate table")
                try:
                    db.engine.execute(
                        "ALTER TABLE affiliate ADD COLUMN user_id INTEGER REFERENCES user(id)"
                    )
                    logger.info("Successfully added user_id column")
                except Exception as e:
                    logger.error(f"Error adding user_id column: {str(e)}")
                    return False
            
            # Update existing affiliates with matching user_id based on email
            logger.info("Linking affiliates to users by matching email addresses")
            
            linked_count = 0
            
            # Get all affiliates without a user_id
            unlinked_affiliates = db.session.execute(
                "SELECT id, email FROM affiliate WHERE user_id IS NULL"
            ).fetchall()
            
            for affiliate_id, affiliate_email in unlinked_affiliates:
                # Find user with matching email
                user = User.query.filter_by(email=affiliate_email).first()
                
                if user:
                    try:
                        db.engine.execute(
                            "UPDATE affiliate SET user_id = :user_id WHERE id = :affiliate_id",
                            {"user_id": user.id, "affiliate_id": affiliate_id}
                        )
                        linked_count += 1
                    except Exception as e:
                        logger.error(f"Error linking affiliate {affiliate_id} to user {user.id}: {str(e)}")
                else:
                    logger.warning(f"No matching user found for affiliate {affiliate_id} with email {affiliate_email}")
            
            logger.info(f"Successfully linked {linked_count} out of {len(unlinked_affiliates)} affiliates to users")
            return True
            
    except Exception as e:
        logger.error(f"Error running affiliate user_id migration: {str(e)}")
        return False