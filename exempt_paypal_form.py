"""
Script to specifically exempt the PayPal email update form from CSRF validation.
This is a targeted solution that should work regardless of Cloudflare configuration.
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

def exempt_paypal_form():
    """Update app.py to exempt the PayPal email update endpoint from CSRF validation"""
    app_py_path = 'app.py'
    
    try:
        # Create backup
        if not backup_file(app_py_path):
            logger.error("Aborting due to backup failure")
            return False
        
        with open(app_py_path, 'r') as f:
            content = f.read()
        
        # Find the initialization of csrf
        csrf_line = "csrf = CSRFProtect(app)"
        
        if csrf_line not in content:
            logger.error("Could not find CSRF initialization in app.py")
            return False
        
        # Look for existing csrf.exempt lines
        if "csrf.exempt('affiliate.update_paypal_email')" in content:
            logger.info("PayPal form is already exempt from CSRF validation")
            return True
        
        # Find a good place to add our exemption - after other exemptions if they exist
        webhook_exempt = "csrf.exempt('billing.stripe_webhook')"
        
        if webhook_exempt in content:
            # Add our exemption after an existing one
            new_content = content.replace(
                webhook_exempt, 
                webhook_exempt + "\n    csrf.exempt('affiliate.update_paypal_email')  # Exempt PayPal email update form"
            )
        else:
            # No existing exemptions, add after csrf initialization
            new_content = content.replace(
                csrf_line,
                csrf_line + "\n\n# Exempt specific endpoints from CSRF validation\ncsrf.exempt('affiliate.update_paypal_email')  # PayPal email update form"
            )
        
        # Write the updated file
        with open(app_py_path, 'w') as f:
            f.write(new_content)
        
        logger.info("Successfully exempted PayPal email update form from CSRF validation")
        return True
    except Exception as e:
        logger.error(f"Error updating app.py: {e}")
        return False

def main():
    """Apply CSRF exemption for PayPal form"""
    logger.info("Starting PayPal form CSRF exemption")
    
    if not exempt_paypal_form():
        logger.error("Failed to exempt PayPal form from CSRF validation")
        return False
    
    logger.info("PayPal form CSRF exemption completed successfully")
    return True

if __name__ == "__main__":
    main()