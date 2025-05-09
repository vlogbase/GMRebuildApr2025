"""
Script to test the admin dashboard functionality.
This runs the Flask application with admin access enabled.
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
log_file = f"admin_output.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run():
    """
    Run tests for admin dashboard functionality.
    """
    logger.info(f"Starting admin dashboard test workflow at {datetime.now().isoformat()}")
    
    try:
        # Ensure admin access for testing
        os.environ['ADMIN_EMAILS'] = 'test@example.com,andy@sentigral.com'
        logger.info(f"Admin emails set to: {os.environ.get('ADMIN_EMAILS')}")
        
        # Run the debug script
        logger.info("Running admin tab debug script")
        import debug_admin_tab
        debug_admin_tab.main()
        
        logger.info("Admin dashboard test completed successfully")
    except Exception as e:
        logger.error(f"Error in admin dashboard test: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run()