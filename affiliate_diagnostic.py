"""
Diagnostic script to investigate affiliate-related issues.
This will check affiliate records and test updating PayPal emails.
"""

import os
import sys
import logging
from datetime import datetime
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_affiliate_records():
    """Check for any affiliate records that might be causing issues"""
    try:
        # Import database models here to avoid circular imports
        from database import db
        from models import User, Affiliate
        
        # Get all affiliate records
        affiliates = Affiliate.query.all()
        logger.info(f"Total affiliate records: {len(affiliates)}")
        
        # Check for duplicates or status issues
        user_ids = {}
        emails = {}
        status_counts = {'active': 0, 'pending': 0, 'awaiting_terms': 0, 'other': 0}
        
        for aff in affiliates:
            # Check for duplicate user_id
            if aff.user_id in user_ids:
                logger.warning(f"Duplicate user_id: {aff.user_id} (Affiliate IDs: {user_ids[aff.user_id]}, {aff.id})")
            else:
                user_ids[aff.user_id] = aff.id
                
            # Check for duplicate email
            if aff.email in emails:
                logger.warning(f"Duplicate email: {aff.email} (Affiliate IDs: {emails[aff.email]}, {aff.id})")
            else:
                emails[aff.email] = aff.id
                
            # Check status
            if aff.status == 'active':
                status_counts['active'] += 1
            elif aff.status == 'pending':
                status_counts['pending'] += 1
            elif aff.status == 'awaiting_terms':
                status_counts['awaiting_terms'] += 1
            else:
                status_counts['other'] += 1
                logger.warning(f"Unusual status: {aff.status} (Affiliate ID: {aff.id})")
        
        logger.info(f"Status counts: {status_counts}")
        
        # Check specific user
        test_email = 'andysurtees924@gmail.com'
        user = User.query.filter_by(email=test_email).first()
        if user:
            logger.info(f"Found user: ID={user.id}, username={user.username}, email={user.email}")
            
            # Check their affiliate record
            affiliate = Affiliate.query.filter_by(user_id=user.id).first()
            if affiliate:
                logger.info(f"Found affiliate record: ID={affiliate.id}, status={affiliate.status}, paypal_email={affiliate.paypal_email}")
            else:
                affiliate = Affiliate.query.filter_by(email=user.email).first()
                if affiliate:
                    logger.info(f"Found affiliate by email: ID={affiliate.id}, status={affiliate.status}, paypal_email={affiliate.paypal_email}")
                else:
                    logger.warning(f"No affiliate record found for user {user.id}")
        else:
            logger.warning(f"User not found with email {test_email}")
            
        return True
    except Exception as e:
        logger.error(f"Error checking affiliate records: {e}", exc_info=True)
        return False

def fix_all_affiliate_statuses():
    """Fix all affiliate statuses to be 'active'"""
    try:
        # Import database models here to avoid circular imports
        from database import db
        from models import User, Affiliate
        
        # Get all non-active affiliates
        non_active = Affiliate.query.filter(Affiliate.status != 'active').all()
        logger.info(f"Found {len(non_active)} non-active affiliate records")
        
        # Update all to active
        count = 0
        for aff in non_active:
            logger.info(f"Updating affiliate ID {aff.id} from '{aff.status}' to 'active'")
            aff.status = 'active'
            if not aff.terms_agreed_at:
                aff.terms_agreed_at = datetime.now()
            count += 1
        
        db.session.commit()
        logger.info(f"Updated {count} affiliate records to 'active' status")
        return True
    except Exception as e:
        logger.error(f"Error fixing affiliate statuses: {e}", exc_info=True)
        return False

def remove_obsolete_affiliate_routes():
    """Modify the blueprint to prevent obsolete pages from showing"""
    try:
        # Get the affiliate blueprint file
        file_path = 'affiliate_blueprint_fix.py'
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace the register and apply routes with redirects to dashboard
        new_register_route = """
@affiliate_bp.route('/register', methods=['GET', 'POST'])
def register():
    \"\"\"Always redirect to dashboard - obsolete route\"\"\"
    logger.info("Redirecting from obsolete /register route to dashboard")
    if 'user_id' not in session:
        flash('Please login to access your affiliate dashboard', 'warning')
        return redirect(url_for('login'))
    
    # Ensure affiliate record exists
    from database import db
    from models import User, Affiliate
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # Get or create affiliate
    affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    if not affiliate:
        affiliate = Affiliate.query.filter_by(email=user.email).first()
    
    if not affiliate:
        # Create new affiliate
        referral_code = str(uuid.uuid4())[:8]
        affiliate = Affiliate(
            user_id=user_id,
            name=user.username,
            email=user.email,
            paypal_email=user.email,
            referral_code=referral_code,
            status='active',
            terms_agreed_at=datetime.now()
        )
        db.session.add(affiliate)
        db.session.commit()
        flash('Your affiliate account has been created!', 'success')
    
    return redirect(url_for('affiliate.dashboard'))
"""
        
        new_apply_route = """
@affiliate_bp.route('/apply', methods=['GET'])
def apply():
    \"\"\"Always redirect to dashboard - obsolete route\"\"\"
    logger.info("Redirecting from obsolete /apply route to dashboard")
    return redirect(url_for('affiliate.dashboard'))
"""
        
        # Find and replace the register route
        import re
        register_pattern = r'@affiliate_bp\.route\(\'/register\',.*?def register\(\):.*?return.*?\n\n'
        if re.search(register_pattern, content, re.DOTALL):
            content = re.sub(register_pattern, new_register_route + "\n\n", content, flags=re.DOTALL)
        else:
            logger.warning("Could not find register route to replace")
        
        # Find and replace the apply route
        apply_pattern = r'@affiliate_bp\.route\(\'/apply\',.*?def apply\(\):.*?return.*?\n\n'
        if re.search(apply_pattern, content, re.DOTALL):
            content = re.sub(apply_pattern, new_apply_route + "\n\n", content, flags=re.DOTALL)
        else:
            logger.warning("Could not find apply route to replace")
        
        # Write the updated file
        with open(file_path, 'w') as f:
            f.write(content)
        
        logger.info("Successfully updated affiliate routes to prevent obsolete pages")
        return True
    except Exception as e:
        logger.error(f"Error removing obsolete routes: {e}", exc_info=True)
        return False

def main():
    """Run all diagnostic and fix functions"""
    logger.info("Starting affiliate diagnostics")
    
    # Check affiliate records
    logger.info("Checking affiliate records...")
    check_affiliate_records()
    
    # Fix all affiliate statuses
    logger.info("Fixing affiliate statuses...")
    fix_all_affiliate_statuses()
    
    # Remove obsolete routes
    logger.info("Removing obsolete routes...")
    remove_obsolete_affiliate_routes()
    
    logger.info("Affiliate diagnostics completed")
    return True

if __name__ == "__main__":
    main()