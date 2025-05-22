"""
Update billing.py to use the simplified affiliate system
"""
import os
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_billing_file():
    """Read the billing.py file"""
    try:
        with open('billing.py', 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        logger.error(f"Error reading billing.py: {e}")
        return None

def backup_billing_file(content):
    """Create a backup of billing.py"""
    try:
        backup_path = f"billing.py.bak.{int(time.time())}"
        with open(backup_path, 'w') as f:
            f.write(content)
        logger.info(f"Created backup of billing.py at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return False

def update_import_statements(content):
    """Update import statements to remove Affiliate imports"""
    try:
        # Replace imports referencing Affiliate
        updated_content = content.replace(
            "from models import User, Transaction, TransactionStatus, Commission, CommissionStatus, Affiliate, CustomerReferral",
            "from models import User, Transaction, TransactionStatus, Commission, CommissionStatus, CustomerReferral"
        )
        
        return updated_content
    except Exception as e:
        logger.error(f"Error updating import statements: {e}")
        return content

def update_commission_processing(content):
    """Update commission processing functions to use User instead of Affiliate"""
    try:
        # Replace instances of Affiliate model with User model
        updated_content = content
        
        # Replace direct references to Affiliate
        updated_content = updated_content.replace(
            "affiliate = Affiliate.query.filter_by(user_id=referring_user.id).first()",
            "affiliate = referring_user  # Using User model directly"
        )
        
        # Replace affiliate.user_id with affiliate.id
        updated_content = updated_content.replace("affiliate.user_id", "affiliate.id")
        
        # Replace affiliate_id with user_id
        updated_content = updated_content.replace("affiliate_id", "user_id")
        
        # Update any status checks (simplified system doesn't need status checks)
        updated_content = updated_content.replace(
            "if affiliate and affiliate.status == 'active':",
            "if affiliate:  # All users with referral codes are active affiliates"
        )
        
        return updated_content
    except Exception as e:
        logger.error(f"Error updating commission processing: {e}")
        return content

def update_customer_referral_handling(content):
    """Update customer referral handling to use User model directly"""
    try:
        # Replace any references to finding affiliates by referral code
        updated_content = content.replace(
            "affiliate = Affiliate.query.filter_by(referral_code=referral_code).first()",
            "referring_user = User.query.filter_by(referral_code=referral_code).first()"
        )
        
        # Update code that sets up referral relationships
        updated_content = updated_content.replace(
            "user.referred_by_affiliate_id = affiliate.id",
            "user.referred_by_user_id = referring_user.id"
        )
        
        return updated_content
    except Exception as e:
        logger.error(f"Error updating customer referral handling: {e}")
        return content

def update_tell_friend_tab(content):
    """Update tell-a-friend tab handling to use User model directly"""
    try:
        # This function will update any references to affiliate status or fields in the tell-a-friend tab
        updated_content = content
        
        # Replace any code checking if a user is an affiliate
        updated_content = updated_content.replace(
            "affiliate = Affiliate.query.filter_by(user_id=current_user.id).first()",
            "# No need to query for affiliate - using User model directly"
        )
        
        # Replace affiliate status checks
        updated_content = updated_content.replace(
            "if affiliate and affiliate.status == 'active':",
            "# All users are potential affiliates now"
        )
        
        # Replace referral code access
        updated_content = updated_content.replace(
            "affiliate.referral_code", 
            "current_user.referral_code"
        )
        
        return updated_content
    except Exception as e:
        logger.error(f"Error updating tell friend tab: {e}")
        return content

def main():
    """Update billing.py with all changes"""
    logger.info("Starting billing.py update")
    
    # Read the billing file
    content = read_billing_file()
    if not content:
        return False
    
    # Create backup
    if not backup_billing_file(content):
        return False
    
    # Update import statements
    updated_content = update_import_statements(content)
    
    # Update commission processing
    updated_content = update_commission_processing(updated_content)
    
    # Update customer referral handling
    updated_content = update_customer_referral_handling(updated_content)
    
    # Update tell-a-friend tab
    updated_content = update_tell_friend_tab(updated_content)
    
    # Write updated content
    try:
        with open('billing.py', 'w') as f:
            f.write(updated_content)
        logger.info("Successfully updated billing.py")
        return True
    except Exception as e:
        logger.error(f"Error writing billing.py: {e}")
        return False

if __name__ == "__main__":
    main()