"""
Direct database script to force all affiliate accounts to active status
"""
import os
import sys
import psycopg2
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_affiliates():
    """Update all affiliate statuses to active using direct SQL"""
    # Get database connection string from environment
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Check how many affiliates are not active
        cursor.execute("SELECT COUNT(*) FROM affiliate WHERE status != 'active'")
        count = cursor.fetchone()[0]
        logger.info(f"Found {count} non-active affiliate records")
        
        # Update all affiliates to active status
        cursor.execute("UPDATE affiliate SET status = 'active' WHERE status != 'active'")
        updated = cursor.rowcount
        logger.info(f"Updated {updated} affiliate records to active status")
        
        # Add terms_agreed_at date for any affiliates missing it
        current_time = datetime.now().isoformat()
        cursor.execute("UPDATE affiliate SET terms_agreed_at = %s WHERE terms_agreed_at IS NULL", (current_time,))
        terms_updated = cursor.rowcount
        logger.info(f"Added terms_agreed_at date for {terms_updated} affiliate records")
        
        # Commit changes
        conn.commit()
        logger.info("Changes committed successfully")
        
        # List all affiliates for verification
        cursor.execute("SELECT id, user_id, email, status, terms_agreed_at FROM affiliate LIMIT 10")
        for row in cursor.fetchall():
            logger.info(f"Affiliate ID: {row[0]}, User ID: {row[1]}, Email: {row[2]}, Status: {row[3]}, Terms Agreed: {row[4]}")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error updating affiliate statuses: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    fix_affiliates()