"""
Script to update the Package model with test mode Stripe price IDs.
This is used for development and testing purposes.
"""

import os
import sys
import logging
import stripe
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_test_price_ids():
    """Return the predefined test price IDs."""
    # Use the provided test mode price IDs
    price_ids = {
        'price_5': 'price_1RKOl0CkgfcNKUGFhI5RljJd',    # Starter Credit Pack ($5.00 USD)
        'price_10': 'price_1RKPmfCkgfcNKUGF7gGqpbZw',   # Small Credit Pack ($10.00 USD)
        'price_25': 'price_1RKPnNCkgfcNKUGFEX9QPfeZ',   # Medium Credit Pack ($25.00 USD)
        'price_100': 'price_1RKPnsCkgfcNKUGFbbHPzUj0',  # Large Credit Pack ($100.00 USD)
    }
    
    logger.info("Using predefined test price IDs")
    return price_ids

def update_database_prices(price_ids):
    """Update the Package model with test price IDs."""
    try:
        # Import here to avoid circular imports
        from app import db
        from models import Package
        
        # Update packages
        packages = Package.query.all()
        
        for package in packages:
            if package.amount_usd == 5:
                package.stripe_price_id = price_ids['price_5']
            elif package.amount_usd == 10:
                package.stripe_price_id = price_ids['price_10']
            elif package.amount_usd == 25:
                package.stripe_price_id = price_ids['price_25']
            elif package.amount_usd == 100:
                package.stripe_price_id = price_ids['price_100']
        
        # Save changes
        db.session.commit()
        
        logger.info("Database packages updated with test price IDs")
        return True
    
    except Exception as e:
        logger.error(f"Error updating database prices: {e}")
        return False

def run():
    """Run the script."""
    try:
        logger.info("Getting predefined test price IDs...")
        price_ids = get_test_price_ids()
        
        logger.info("Updating database with test price IDs...")
        result = update_database_prices(price_ids)
        
        if result:
            logger.info("Successfully updated packages with test price IDs:")
            logger.info(f"Starter Package ($5): {price_ids['price_5']}")
            logger.info(f"Small Package ($10): {price_ids['price_10']}")
            logger.info(f"Medium Package ($25): {price_ids['price_25']}")
            logger.info(f"Large Package ($100): {price_ids['price_100']}")
            return True
        else:
            logger.error("Failed to update database with test price IDs")
            return False
    
    except Exception as e:
        logger.error(f"Error running script: {e}")
        return False

if __name__ == "__main__":
    success = run()
    
    if success:
        print("Database updated with test price IDs successfully")
        sys.exit(0)
    else:
        print("Failed to update database with test price IDs")
        sys.exit(1)