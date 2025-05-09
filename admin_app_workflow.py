"""
Simple script to run the Flask application with admin privileges for testing.
"""

import os
import sys
import logging
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with admin access enabled.
    """
    try:
        # Set admin credentials in the environment
        os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com,test@example.com'
        logger.info(f"Admin mode enabled. ADMIN_EMAILS set to: {os.environ.get('ADMIN_EMAILS')}")
        
        # Print admin route details for testing
        logger.info("Admin routes available:")
        logger.info(f"- Main Admin Dashboard: /admin/dashboard")
        logger.info(f"- Admin Commissions Management: /affiliate/admin/commissions")
        logger.info(f"- Admin Payouts Processing: /affiliate/admin/payouts")
        logger.info(f"- Account Page with Admin Tab: /billing/account?tab=admin")
        
        # Start the Flask application
        logger.info("Starting Flask application with ADMIN MODE enabled")
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"Failed to start admin mode: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()