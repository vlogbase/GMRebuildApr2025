"""
Run script for Stripe database migrations.
This script runs the migrations to update the database schema for Stripe integration.
"""

import os
import sys
import logging
from migrations_stripe import run_migrations
from update_stripe_test_prices import run as update_prices

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    """Run Stripe database migrations and update package prices."""
    try:
        # Check for required environment variables
        if not os.environ.get('DATABASE_URL'):
            logger.error("DATABASE_URL not found in environment variables")
            return False
        
        if not os.environ.get('STRIPE_SECRET_KEY'):
            logger.error("STRIPE_SECRET_KEY not found in environment variables")
            return False
        
        # Run migrations
        logger.info("Running Stripe database migrations...")
        if not run_migrations():
            logger.error("Failed to run Stripe database migrations")
            return False
        
        # Update package prices
        logger.info("Updating package prices with test mode price IDs...")
        if not update_prices():
            logger.error("Failed to update package prices with test mode price IDs")
            return False
        
        logger.info("Stripe database setup completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error running Stripe database setup: {e}")
        return False

if __name__ == "__main__":
    success = run()
    
    if success:
        print("Stripe database setup completed successfully")
        sys.exit(0)
    else:
        print("Failed to run Stripe database setup")
        sys.exit(1)