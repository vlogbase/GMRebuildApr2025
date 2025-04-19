"""
Flask workflow script to run the application with proper configuration in Replit.
This script ensures migrations are run before starting the application.
"""
import os
import sys
import logging
from migrations_google_auth import run_migration as run_google_auth_migration
from migrations_payment_system import run_migration as run_payment_system_migration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to run the Flask application.
    1. Run migrations
    2. Start the Flask app
    """
    logger.info("Starting Flask workflow")
    
    # Check for required environment variables
    if not os.environ.get("GOOGLE_OAUTH_CLIENT_ID"):
        logger.warning("GOOGLE_OAUTH_CLIENT_ID is not set. Google login will not work.")
    
    if not os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET"):
        logger.warning("GOOGLE_OAUTH_CLIENT_SECRET is not set. Google login will not work.")
    
    # Run migrations
    logger.info("Running Google Auth migration...")
    google_auth_success = run_google_auth_migration()
    if not google_auth_success:
        logger.error("Google Auth migration failed. Please check the logs for details.")
    else:
        logger.info("Google Auth migration completed successfully")
    
    logger.info("Running Payment System migration...")
    payment_system_success = run_payment_system_migration()
    if not payment_system_success:
        logger.error("Payment System migration failed. Please check the logs for details.")
    else:
        logger.info("Payment System migration completed successfully")
        
    # Check for PayPal credentials
    if not os.environ.get("PAYPAL_CLIENT_ID") or not os.environ.get("PAYPAL_CLIENT_SECRET"):
        logger.warning("PayPal credentials are missing. Payment functionality will be limited.")
    
    # Import and run the Flask app
    logger.info("Starting Flask application...")
    from app import app
    
    # Get the port from the environment or use 5000 as a default
    port = int(os.environ.get("PORT", 5000))
    
    # Run the app
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()