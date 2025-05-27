#!/usr/bin/env python3
"""
Direct Database Migration: Add ELO Score Column

A lightweight script to add the elo_score column directly to the database
without full app initialization overhead.
"""

import os
import logging
import psycopg2
from contextlib import contextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """Get a direct database connection using the DATABASE_URL"""
    connection = None
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL environment variable not found")
        
        connection = psycopg2.connect(database_url)
        yield connection
        
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if connection:
            connection.close()

def check_column_exists():
    """Check if the elo_score column already exists"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='open_router_model' 
            AND column_name='elo_score';
        """)
        result = cursor.fetchone()
        cursor.close()
        return result is not None

def add_elo_column():
    """Add the elo_score column to the open_router_model table"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Add the column
        cursor.execute("""
            ALTER TABLE open_router_model 
            ADD COLUMN elo_score INTEGER;
        """)
        
        conn.commit()
        cursor.close()
        return True

def verify_column():
    """Verify the column was added successfully"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total_models,
                   COUNT(elo_score) as models_with_elo
            FROM open_router_model;
        """)
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            total_models, models_with_elo = result
            logger.info(f"Verification: {total_models} total models, {models_with_elo} have ELO scores")
            return True
        return False

def main():
    """Run the migration"""
    logger.info("Adding elo_score column to open_router_model table...")
    
    try:
        # Check if column already exists
        if check_column_exists():
            logger.info("✅ elo_score column already exists - no migration needed")
            return True
        
        # Add the column
        add_elo_column()
        logger.info("✅ Successfully added elo_score column")
        
        # Verify
        if verify_column():
            logger.info("✅ Migration completed and verified successfully!")
            return True
        else:
            logger.error("❌ Migration verification failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)