#!/usr/bin/env python3
"""
Run all affiliate system migrations in the correct order.
This script sets up the database tables for the affiliate system.
"""

import os
import logging
import traceback
from app import app, db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_migrations():
    """Run all affiliate migrations in the correct order"""
    
    try:
        # First run the initial affiliate migrations
        logger.info("Running initial affiliate migrations...")
        from migrations_affiliate import run_migrations as run_initial_migrations
        
        with app.app_context():
            success = run_initial_migrations()
            if success:
                logger.info("✅ Initial affiliate migrations completed successfully!")
            else:
                logger.error("❌ Initial affiliate migrations failed!")
                return False
        
        # Then run the affiliate update migrations
        logger.info("Running affiliate update migrations...")
        from migrations_affiliate_update import run_migrations as run_update_migrations
        
        with app.app_context():
            success = run_update_migrations()
            if success:
                logger.info("✅ Affiliate update migrations completed successfully!")
            else:
                logger.error("❌ Affiliate update migrations failed!")
                return False
        
        logger.info("✅ All affiliate migrations completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = run_migrations()
    
    if success:
        print("✅ All affiliate migrations completed successfully!")
        
        # Verify the tables exist
        with app.app_context():
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables in database: {tables}")
            
            affiliate_tables = [t for t in tables if 'affiliate' in t or 'commission' in t or 'referral' in t]
            print(f"Affiliate-related tables: {affiliate_tables}")
    else:
        print("❌ Affiliate migrations failed! Check the logs for details.")