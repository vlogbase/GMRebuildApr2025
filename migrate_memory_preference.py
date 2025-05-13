"""
One-time migration script to set enable_memory=True for all existing users.
This ensures backward compatibility after adding the enable_memory field to the User model.
"""

import logging
from app import app, db
from models import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_users():
    """
    Update all users to set enable_memory=True as the default.
    """
    with app.app_context():
        try:
            # Get all users
            users = User.query.all()
            logger.info(f"Found {len(users)} users to migrate")
            
            # Count users without enable_memory set
            updated_count = 0
            
            # Update each user
            for user in users:
                # Check if enable_memory is already set (could be None or not present)
                if not hasattr(user, 'enable_memory') or user.enable_memory is None:
                    user.enable_memory = True
                    updated_count += 1
            
            # Commit changes
            if updated_count > 0:
                db.session.commit()
                logger.info(f"Successfully updated {updated_count} users with enable_memory=True")
            else:
                logger.info("No users needed updating")
                
            return True
            
        except Exception as e:
            logger.error(f"Error migrating users: {e}")
            return False

if __name__ == "__main__":
    logger.info("Starting user migration for enable_memory field")
    success = migrate_users()
    if success:
        logger.info("Migration completed successfully")
    else:
        logger.error("Migration failed")