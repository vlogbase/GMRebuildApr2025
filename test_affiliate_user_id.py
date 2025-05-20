"""
Simple test script to verify that the affiliate system is working
with the new user_id field.
"""

import os
import logging
from datetime import datetime
from flask import Flask
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main test function"""
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            return False
            
        logger.info("Connecting to database...")
        engine = create_engine(database_url)
        
        # Check if user_id column exists in affiliate table
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT column_name FROM information_schema.columns "
                                         "WHERE table_name='affiliate' AND column_name='user_id'"))
                has_user_id = result.rowcount > 0
                
                if has_user_id:
                    logger.info("✅ user_id column exists in affiliate table")
                    
                    # Find affiliates with and without user_id
                    result = conn.execute(text("SELECT COUNT(*) FROM affiliate"))
                    total_count = result.scalar()
                    
                    result = conn.execute(text("SELECT COUNT(*) FROM affiliate WHERE user_id IS NOT NULL"))
                    linked_count = result.scalar()
                    
                    result = conn.execute(text("SELECT COUNT(*) FROM affiliate WHERE user_id IS NULL"))
                    unlinked_count = result.scalar()
                    
                    logger.info(f"Total affiliates: {total_count}")
                    logger.info(f"Affiliates linked to users: {linked_count}")
                    logger.info(f"Affiliates not linked to users: {unlinked_count}")
                    
                    if linked_count > 0:
                        # Show some sample data (first 5 rows)
                        result = conn.execute(text(
                            "SELECT a.id, a.name, a.email, a.user_id, u.username, u.email "
                            "FROM affiliate a "
                            "JOIN \"user\" u ON a.user_id = u.id "
                            "LIMIT 5"
                        ))
                        
                        logger.info("Sample of linked affiliates:")
                        for row in result:
                            logger.info(f"Affiliate ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, "
                                       f"User ID: {row[3]}, Username: {row[4]}, User Email: {row[5]}")
                else:
                    logger.error("❌ user_id column does not exist in affiliate table")
                    return False
                    
                return True
                
        except Exception as e:
            logger.error(f"Error checking database: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error in test script: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Test completed successfully")
    else:
        logger.error("Test failed")