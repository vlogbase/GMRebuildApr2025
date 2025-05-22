"""
Generate referral codes for all users who don't have one

This script ensures that every user has a unique referral code, making everyone
automatically part of the simplified affiliate program.
"""
import os
import sys
import logging
import random
import string
from datetime import datetime

from app import app, db
from models import User

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_unique_referral_code():
    """Generate a unique 8-character referral code"""
    # Keep trying until we find an unused code
    while True:
        # Generate a random string of 8 characters (letters and numbers)
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Check if this code is already in use
        existing = User.query.filter(User.referral_code == code).first()
        if not existing:
            return code

def generate_referral_codes():
    """Generate referral codes for all users who don't have one"""
    with app.app_context():
        # Get count of users without referral codes
        users_without_codes = User.query.filter(
            (User.referral_code == None) | (User.referral_code == '')
        ).count()
        
        logger.info(f"Found {users_without_codes} users without referral codes")
        
        # Get all users without referral codes
        users = User.query.filter(
            (User.referral_code == None) | (User.referral_code == '')
        ).all()
        
        # Generate and assign referral codes
        for user in users:
            code = generate_unique_referral_code()
            user.referral_code = code
            logger.info(f"Generated referral code {code} for user {user.id} ({user.username})")
        
        # Commit all changes
        db.session.commit()
        
        logger.info(f"Successfully generated referral codes for {len(users)} users")
        
        # Verify the results
        remaining_users_without_codes = User.query.filter(
            (User.referral_code == None) | (User.referral_code == '')
        ).count()
        
        logger.info(f"Users still without referral codes: {remaining_users_without_codes}")
        
        # Show some examples
        sample_users = User.query.limit(5).all()
        if sample_users:
            logger.info("Sample users with referral codes:")
            for user in sample_users:
                logger.info(f"- User {user.id} ({user.username}): {user.referral_code}")

if __name__ == "__main__":
    generate_referral_codes()