"""
Direct update script for Stripe price IDs in the database.
This script connects directly to the database without loading the full Flask app.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, MetaData, Table, Column, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_price_ids():
    """Update the Package table with live Stripe price IDs."""
    try:
        # Get database URL from environment
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL not found in environment")
            return False
        
        # Connect to database
        engine = create_engine(db_url)
        
        # Define the price ID mappings
        price_ids = {
            5: 'price_1RKNWECkgfcNKUGFdQh7RdkG',    # $5 package
            10: 'price_1RKMr3CkgfcNKUGF59u652tm',   # $10 package
            25: 'price_1RKNZPCkgfcNKUGFvCDiMTsH',   # $25 package
            100: 'price_1RKNa6CkgfcNKUGFHbhsa1w0',  # $100 package
        }
        
        # Use a transaction to safely update prices
        with engine.begin() as conn:
            # Get packages from database
            packages_query = text("SELECT id, amount_usd, stripe_price_id FROM package")
            packages = conn.execute(packages_query).fetchall()
            
            # Update each package
            for package in packages:
                package_id = package[0]
                amount_usd = package[1]
                old_price_id = package[2]
                
                if amount_usd in price_ids:
                    new_price_id = price_ids[amount_usd]
                    
                    # Update the price ID
                    update_query = text(
                        "UPDATE package SET stripe_price_id = :new_price_id WHERE id = :package_id"
                    )
                    conn.execute(update_query, {"new_price_id": new_price_id, "package_id": package_id})
                    
                    logger.info(f"Updated ${amount_usd} package (ID: {package_id}) price ID from {old_price_id} to {new_price_id}")
        
        logger.info("Successfully updated all package price IDs to live mode")
        return True
    
    except Exception as e:
        logger.error(f"Error updating price IDs: {e}")
        return False

if __name__ == "__main__":
    success = update_price_ids()
    
    if success:
        print("Successfully updated all package price IDs to live mode")
        sys.exit(0)
    else:
        print("Failed to update package price IDs")
        sys.exit(1)