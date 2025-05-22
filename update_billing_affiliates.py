"""
Update billing.py to use User model for affiliate features
"""
import os
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_imports():
    """Update imports in billing.py"""
    try:
        # Read the file
        with open('billing.py', 'r') as f:
            content = f.read()
        
        # Backup the file
        backup_path = f"billing.py.bak.{int(time.time())}"
        with open(backup_path, 'w') as f:
            f.write(content)
        logger.info(f"Created backup of billing.py at {backup_path}")
        
        # Update imports
        old_import = "from models import CustomerReferral, Affiliate, Commission, CommissionStatus, AffiliateStatus"
        new_import = "from models import CustomerReferral, Commission, CommissionStatus, AffiliateStatus"
        
        content = content.replace(old_import, new_import)
        
        # Write updated content
        with open('billing.py', 'w') as f:
            f.write(content)
        
        logger.info("Updated imports in billing.py")
        return True
    except Exception as e:
        logger.error(f"Error updating imports: {e}")
        return False

def update_affiliate_references():
    """Update references to Affiliate model in billing.py"""
    try:
        # Read the file
        with open('billing.py', 'r') as f:
            content = f.read()
        
        # Update affiliate query
        old_code = """
        affiliate = Affiliate.query.filter_by(email=current_user.email).first()
        if not affiliate:
            # Auto-create affiliate if user doesn't have one
            affiliate = Affiliate.auto_create_for_user(current_user)
"""
        new_code = """
        # User model now has affiliate fields directly
        affiliate = current_user
"""
        content = content.replace(old_code, new_code)
        
        # Update join for referrals
        old_join = """
                User, User.email == Affiliate.email
            ).join(
                Affiliate, 
                Affiliate.referred_by_affiliate_id == affiliate.id
            ).order_by(
                Affiliate.id
            )"""
        
        new_join = """
                User, 
                User.referred_by_user_id == current_user.id
            ).order_by(
                User.id
            )"""
        
        content = content.replace(old_join, new_join)
        
        # Update referral logic for commissions
        old_referral_code = """
        l1_affiliate = Affiliate.query.get(customer_referral.affiliate_id)
        if l1_affiliate and l1_affiliate.referred_by_affiliate_id:
            l2_affiliate = Affiliate.query.get(l1_affiliate.referred_by_affiliate_id)
            if l2_affiliate:
                # Create tier 2 commission
"""
        
        new_referral_code = """
        l1_user = User.query.get(customer_referral.user_id)
        if l1_user and l1_user.referred_by_user_id:
            l2_user = User.query.get(l1_user.referred_by_user_id)
            if l2_user:
                # Create tier 2 commission
"""
        
        content = content.replace(old_referral_code, new_referral_code)
        
        # Write updated content
        with open('billing.py', 'w') as f:
            f.write(content)
        
        logger.info("Updated affiliate references in billing.py")
        return True
    except Exception as e:
        logger.error(f"Error updating affiliate references: {e}")
        return False

def main():
    """Run all updates"""
    logger.info("Starting billing.py update")
    
    # Update imports
    if not update_imports():
        logger.error("Failed to update imports")
        return False
    
    # Update affiliate references
    if not update_affiliate_references():
        logger.error("Failed to update affiliate references")
        return False
    
    logger.info("Successfully updated billing.py")
    return True

if __name__ == "__main__":
    main()