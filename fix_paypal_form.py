"""
Script to fix the PayPal email update form in the affiliate system.

This script:
1. Updates app.py to import the fixed affiliate blueprint
2. Verifies the template has the correct form action
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_file(file_path):
    """Create a backup of a file before modifying it"""
    backup_path = f"{file_path}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        with open(file_path, 'r') as original:
            with open(backup_path, 'w') as backup:
                backup.write(original.read())
        logger.info(f"Created backup of {file_path} at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup of {file_path}: {e}")
        return False

def update_app_py():
    """Update app.py to use the fixed affiliate blueprint"""
    app_py_path = 'app.py'
    
    try:
        # Create backup
        if not backup_file(app_py_path):
            logger.error("Aborting due to backup failure")
            return False
        
        with open(app_py_path, 'r') as f:
            content = f.read()
        
        # Update the import statement
        new_content = content.replace(
            "from affiliate_blueprint_improved import init_app as init_affiliate_bp",
            "from affiliate_blueprint_fix import init_app as init_affiliate_bp"
        )
        
        # Write the updated file
        with open(app_py_path, 'w') as f:
            f.write(new_content)
        
        logger.info("Successfully updated app.py to use the fixed affiliate blueprint")
        return True
    except Exception as e:
        logger.error(f"Error updating app.py: {e}")
        return False

def check_template():
    """Verify the template has the correct form action"""
    template_path = 'templates/affiliate/tell_friend_tab.html'
    
    try:
        with open(template_path, 'r') as f:
            content = f.read()
        
        if 'form action="{{ url_for(\'affiliate.update_paypal_email\') }}"' in content:
            logger.info("Template has the correct form action")
            return True
        else:
            logger.warning("Template doesn't have the correct form action")
            return False
    except Exception as e:
        logger.error(f"Error checking template: {e}")
        return False

def main():
    """Run all the fixes"""
    logger.info("Starting PayPal email form fix")
    
    # Update app.py
    if not update_app_py():
        logger.error("Failed to update app.py")
        return False
    
    # Check template
    if not check_template():
        logger.warning("Template check failed, but continuing")
    
    logger.info("PayPal email form fix completed successfully")
    return True

if __name__ == "__main__":
    main()