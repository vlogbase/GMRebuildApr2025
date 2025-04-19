"""
Flask workflow script to run the application with proper configuration in Replit.
This script ensures the migration is run before starting the application.
"""
import os
import sys
import logging
from migrations_google_auth import run_migration

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
    logger.info("Running database migrations...")
    migration_success = run_migration()
    if not migration_success:
        logger.error("Migration failed. Please check the logs for details.")
    else:
        logger.info("Migration completed successfully")
    
    # Import and run the Flask app
    logger.info("Starting Flask application...")
    from app import app
    
    # Get the port from the environment or use 5000 as a default
    port = int(os.environ.get("PORT", 5000))
    
    # Run the app
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()