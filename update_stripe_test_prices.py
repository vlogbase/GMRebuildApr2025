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

def create_test_prices():
    """Create test prices in Stripe and return their IDs."""
    try:
        # Initialize Stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        if not stripe.api_key:
            logger.error("Stripe API key not found")
            return False
        
        # Create test prices
        price_ids = {}
        
        # Create product first
        product = stripe.Product.create(
            name="Credit Packages",
            description="Packages of credits for the GloriaMundo Chatbot"
        )
        
        # Create prices
        price_5 = stripe.Price.create(
            unit_amount=500,  # $5.00
            currency="usd",
            product=product.id,
            nickname="Starter Credit Pack"
        )
        price_ids['price_5'] = price_5.id
        
        price_10 = stripe.Price.create(
            unit_amount=1000,  # $10.00
            currency="usd",
            product=product.id,
            nickname="Small Credit Pack"
        )
        price_ids['price_10'] = price_10.id
        
        price_25 = stripe.Price.create(
            unit_amount=2500,  # $25.00
            currency="usd",
            product=product.id,
            nickname="Medium Credit Pack"
        )
        price_ids['price_25'] = price_25.id
        
        price_100 = stripe.Price.create(
            unit_amount=10000,  # $100.00
            currency="usd",
            product=product.id,
            nickname="Large Credit Pack"
        )
        price_ids['price_100'] = price_100.id
        
        logger.info(f"Test prices created: {price_ids}")
        return price_ids
    
    except Exception as e:
        logger.error(f"Error creating test prices: {e}")
        return None

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
        logger.info("Creating test prices in Stripe...")
        price_ids = create_test_prices()
        
        if not price_ids:
            logger.error("Failed to create test prices")
            return False
        
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
        print("Test prices created and database updated successfully")
        sys.exit(0)
    else:
        print("Failed to create test prices or update database")
        sys.exit(1)