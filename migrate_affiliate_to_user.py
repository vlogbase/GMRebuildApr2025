"""
Migration script to move affiliate data into the user table and simplify the system
"""
import uuid
import logging
from datetime import datetime
from app import app
from database import db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_columns_to_user_table():
    """Add necessary affiliate columns to the user table"""
    try:
        with app.app_context():
            # Check if columns already exist
            columns = db.session.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'user'").fetchall()
            column_names = [col[0] for col in columns]
            
            logger.info(f"Existing columns in user table: {column_names}")
            
            # Add paypal_email column if it doesn't exist
            if 'paypal_email' not in column_names:
                db.session.execute("ALTER TABLE \"user\" ADD COLUMN paypal_email VARCHAR(255)")
                logger.info("Added paypal_email column to user table")
            
            # Add referral_code column if it doesn't exist
            if 'referral_code' not in column_names:
                db.session.execute("ALTER TABLE \"user\" ADD COLUMN referral_code VARCHAR(20)")
                logger.info("Added referral_code column to user table")
            
            # Add referred_by_user_id column if it doesn't exist
            if 'referred_by_user_id' not in column_names:
                db.session.execute("ALTER TABLE \"user\" ADD COLUMN referred_by_user_id INTEGER")
                logger.info("Added referred_by_user_id column to user table")
            
            db.session.commit()
            logger.info("Successfully added affiliate columns to user table")
            return True
    except Exception as e:
        logger.error(f"Error adding columns to user table: {e}")
        return False

def migrate_affiliate_data():
    """Move data from affiliate table to user table"""
    try:
        with app.app_context():
            # First, get all affiliates with their related users
            from models import Affiliate, User
            
            # Import the necessary SQLAlchemy functions
            from sqlalchemy import text
            
            # Check if any user already has referral codes
            users_with_referral_codes = db.session.execute(
                text("SELECT COUNT(*) FROM \"user\" WHERE referral_code IS NOT NULL")
            ).scalar()
            
            if users_with_referral_codes > 0:
                logger.info(f"Found {users_with_referral_codes} users already with referral codes. Skipping generation.")
            else:
                # Generate referral codes for all users who don't have one
                users = User.query.all()
                for user in users:
                    if not user.referral_code:
                        user.referral_code = str(uuid.uuid4())[:8]
                        logger.info(f"Generated referral code for user {user.id}: {user.referral_code}")
                db.session.commit()
            
            # Count successful migrations
            migration_count = 0
            
            # Now migrate specific affiliate data
            affiliates = Affiliate.query.all()
            logger.info(f"Found {len(affiliates)} affiliate records to migrate")
            
            for affiliate in affiliates:
                # Find the corresponding user by email
                user = User.query.filter_by(email=affiliate.email).first()
                
                if user:
                    logger.info(f"Migrating affiliate ID {affiliate.id} to user ID {user.id}")
                    
                    # Update the user with affiliate data
                    user.paypal_email = affiliate.paypal_email
                    
                    # Only update referral_code if the user doesn't have one yet
                    if not user.referral_code and affiliate.referral_code:
                        user.referral_code = affiliate.referral_code
                    
                    # Handle the referred_by relationship
                    if affiliate.referred_by_affiliate_id:
                        # Find the user ID corresponding to the referring affiliate
                        referring_affiliate = Affiliate.query.get(affiliate.referred_by_affiliate_id)
                        if referring_affiliate:
                            referring_user = User.query.filter_by(email=referring_affiliate.email).first()
                            if referring_user:
                                user.referred_by_user_id = referring_user.id
                                logger.info(f"Set referred_by_user_id to {referring_user.id}")
                    
                    migration_count += 1
                else:
                    logger.warning(f"Could not find user matching affiliate email: {affiliate.email}")
            
            # Commit changes
            db.session.commit()
            logger.info(f"Successfully migrated {migration_count} affiliate records to user table")
            
            return True
    except Exception as e:
        logger.error(f"Error migrating affiliate data: {e}")
        return False

def update_models_py():
    """Update models.py to add the new fields to the User model"""
    try:
        # Read the current models.py file
        with open('models.py', 'r') as f:
            content = f.read()
        
        # Add our new fields to the User model
        user_class_end = "    # Add any additional fields here"
        if user_class_end in content:
            new_fields = """    # Affiliate-related fields
    paypal_email = db.Column(db.String(255))
    referral_code = db.Column(db.String(20), unique=True)
    referred_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Add any additional fields here"""
            
            # Replace the placeholder with our new fields
            updated_content = content.replace(user_class_end, new_fields)
            
            # Write the updated content back to models.py
            with open('models.py', 'w') as f:
                f.write(updated_content)
            
            logger.info("Successfully updated models.py with new fields")
            return True
        else:
            logger.warning("Could not find insertion point in models.py")
            return False
    except Exception as e:
        logger.error(f"Error updating models.py: {e}")
        return False

def main():
    """Run all migration steps"""
    logger.info("Starting affiliate to user migration")
    
    # Update the models.py file
    if update_models_py():
        logger.info("Models updated successfully")
    else:
        logger.warning("Could not update models.py, continuing anyway")
    
    # Add necessary columns to user table
    if add_columns_to_user_table():
        logger.info("Columns added to user table successfully")
    else:
        logger.error("Failed to add columns to user table")
        return False
    
    # Migrate data from affiliate table to user table
    if migrate_affiliate_data():
        logger.info("Affiliate data migrated successfully")
    else:
        logger.error("Failed to migrate affiliate data")
        return False
    
    logger.info("Migration completed successfully")
    return True

if __name__ == "__main__":
    main()