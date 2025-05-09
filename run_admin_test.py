"""
Simple script to run the admin testing dashboard in a deployed Replit environment
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    """Run the admin test application"""
    try:
        # Set up admin credentials in the environment
        os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com,test@example.com'
        logger.info(f"ADMIN_EMAILS set to: {os.environ.get('ADMIN_EMAILS')}")
        
        # Import Flask app here to avoid circular imports
        from app import app
        
        # Print admin route details for testing
        logger.info("Admin route details:")
        logger.info(f"Admin Dashboard: /admin/dashboard")
        logger.info(f"Admin Commissions: /affiliate/admin/commissions")
        logger.info(f"Admin Payouts: /affiliate/admin/payouts")
        
        # Start the Flask application
        logger.info("Starting Flask application for admin testing at http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"Failed to start admin test application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()