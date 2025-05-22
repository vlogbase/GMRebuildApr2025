"""
Generate unique referral codes for all users who don't have one
"""
import os
import logging
from datetime import datetime
from app import app, db
from models import User

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_referral_codes():
    """Generate unique referral codes for all users who don't have one"""
    with app.app_context():
        try:
            # Get all users without a referral code
            users_without_code = User.query.filter(
                (User.referral_code == None) | (User.referral_code == '')
            ).all()
            
            logger.info(f"Found {len(users_without_code)} users without a referral code")
            
            # Generate codes for each user
            for user in users_without_code:
                user.generate_referral_code()
                logger.info(f"Generated referral code {user.referral_code} for user {user.id} ({user.username})")
            
            # Commit changes
            db.session.commit()
            logger.info("Successfully generated referral codes for all users")
            
            # Show summary of users with codes
            total_users = User.query.count()
            users_with_code = User.query.filter(
                User.referral_code != None, 
                User.referral_code != ''
            ).count()
            
            logger.info(f"Summary: {users_with_code}/{total_users} users now have referral codes")
            
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error generating referral codes: {e}")
            return False

if __name__ == "__main__":
    generate_referral_codes()