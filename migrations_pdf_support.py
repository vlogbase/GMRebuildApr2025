"""
Migration script to add the supports_pdf column to the open_router_model table.
"""

import os
import logging
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_pdf_support_column():
    """Add the supports_pdf column to the open_router_model table"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL not found in environment variables")
            return False
        
        logger.info("Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if the column already exists
        logger.info("Checking if supports_pdf column exists...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'open_router_model' 
            AND column_name = 'supports_pdf'
        """)
        column_exists = cursor.fetchone() is not None
        
        if column_exists:
            logger.info("supports_pdf column already exists, skipping migration")
            return True
        
        # Add the column
        logger.info("Adding supports_pdf column to open_router_model table")
        cursor.execute("ALTER TABLE open_router_model ADD COLUMN supports_pdf BOOLEAN DEFAULT FALSE")
        
        # Commit the changes
        conn.commit()
        logger.info("Migration completed successfully")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error migrating database: {e}")
        return False

if __name__ == "__main__":
    add_pdf_support_column()