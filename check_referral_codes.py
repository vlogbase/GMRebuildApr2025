"""
Check referral codes for all users
"""
import os
import logging
from app import app, db
from models import User

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_referral_codes():
    """Check referral codes for all users"""
    with app.app_context():
        total_users = User.query.count()
        users_with_code = User.query.filter(
            User.referral_code.isnot(None), 
            User.referral_code != ''
        ).count()
        
        print(f"Referral Code Status:")
        print(f"- Total users: {total_users}")
        print(f"- Users with referral codes: {users_with_code}")
        print(f"- Users without referral codes: {total_users - users_with_code}")
        print(f"- Coverage: {(users_with_code/total_users)*100:.2f}% of users have referral codes")
        
        # Show some example codes
        sample_users = User.query.filter(User.referral_code.isnot(None)).limit(5).all()
        if sample_users:
            print("\nSample referral codes:")
            for user in sample_users:
                print(f"- User {user.id} ({user.username}): {user.referral_code}")

if __name__ == "__main__":
    check_referral_codes()