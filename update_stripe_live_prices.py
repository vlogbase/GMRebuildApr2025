"""
Script to update the Package model with live mode Stripe price IDs.
This is used for production.
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_live_price_ids():
    """Return the predefined live price IDs."""
    # Use the provided live mode price IDs
    price_ids = {
        'price_5': 'price_1RKNWECkgfcNKUGFdQh7RdkG',    # Starter Credit Pack ($5.00 USD)
        'price_10': 'price_1RKMr3CkgfcNKUGF59u652tm',   # Small Credit Pack ($10.00 USD)
        'price_25': 'price_1RKNZPCkgfcNKUGFvCDiMTsH',   # Medium Credit Pack ($25.00 USD)
        'price_100': 'price_1RKNa6CkgfcNKUGFHbhsa1w0',  # Large Credit Pack ($100.00 USD)
    }
    
    logger.info("Using predefined live price IDs")
    return price_ids

def update_database_prices(price_ids):
    """Update the Package model with live price IDs."""
    try:
        # Import here to avoid circular imports
        from app import db
        from models import Package
        
        # Update packages
        packages = Package.query.all()
        
        for package in packages:
            if package.amount_usd == 5:
                old_id = package.stripe_price_id
                package.stripe_price_id = price_ids['price_5']
                logger.info(f"Updated $5 package price ID from {old_id} to {price_ids['price_5']}")
            elif package.amount_usd == 10:
                old_id = package.stripe_price_id
                package.stripe_price_id = price_ids['price_10']
                logger.info(f"Updated $10 package price ID from {old_id} to {price_ids['price_10']}")
            elif package.amount_usd == 25:
                old_id = package.stripe_price_id
                package.stripe_price_id = price_ids['price_25']
                logger.info(f"Updated $25 package price ID from {old_id} to {price_ids['price_25']}")
            elif package.amount_usd == 100:
                old_id = package.stripe_price_id
                package.stripe_price_id = price_ids['price_100']
                logger.info(f"Updated $100 package price ID from {old_id} to {price_ids['price_100']}")
        
        # Save changes
        db.session.commit()
        
        logger.info("Database packages updated with live price IDs")
        return True
    
    except Exception as e:
        logger.error(f"Error updating database prices: {e}")
        return False

def run():
    """Run the update operation."""
    try:
        # Check for required environment variables
        if not os.environ.get('STRIPE_SECRET_KEY'):
            logger.error("STRIPE_SECRET_KEY not found in environment variables")
            return False
        
        # Get live price IDs
        price_ids = get_live_price_ids()
        
        # Update database
        if not update_database_prices(price_ids):
            return False
        
        logger.info("Stripe live price ID update completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error running Stripe live price update: {e}")
        return False

if __name__ == "__main__":
    success = run()
    
    if success:
        print("Stripe live price ID update completed successfully")
        sys.exit(0)
    else:
        print("Failed to run Stripe live price ID update")
        sys.exit(1)