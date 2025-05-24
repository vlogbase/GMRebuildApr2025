#!/usr/bin/env python3
"""
Database Migration: Add ELO Score Column to OpenRouterModel

This migration adds the elo_score column to the open_router_model table
to store LMSYS Chatbot Arena ELO ratings for model performance ranking.
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import text
from contextlib import contextmanager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to the path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@contextmanager
def app_context():
    """Context manager to provide the Flask app context"""
    try:
        from app import app, db
        with app.app_context():
            yield db
    except Exception as e:
        logger.error(f"Failed to get app context: {e}")
        raise

def check_column_exists():
    """Check if the elo_score column already exists in the table"""
    with app_context() as db:
        try:
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='open_router_model' 
                AND column_name='elo_score';
            """)).fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking if column exists: {e}")
            return False

def add_elo_score_column():
    """Add the elo_score column to the open_router_model table"""
    with app_context() as db:
        try:
            # Add the new column
            logger.info("Adding elo_score column to open_router_model table...")
            db.session.execute(text("""
                ALTER TABLE open_router_model 
                ADD COLUMN elo_score INTEGER;
            """))
            
            # Commit the change
            db.session.commit()
            logger.info("Successfully added elo_score column")
            return True
            
        except Exception as e:
            logger.error(f"Error adding elo_score column: {e}")
            db.session.rollback()
            return False

def verify_migration():
    """Verify that the migration was successful"""
    with app_context() as db:
        try:
            # Check that the column exists and can be queried
            result = db.session.execute(text("""
                SELECT COUNT(*) as model_count,
                       COUNT(elo_score) as models_with_elo
                FROM open_router_model;
            """)).fetchone()
            
            if result:
                total_models = result[0]
                models_with_elo = result[1]
                logger.info(f"Migration verification: {total_models} total models, {models_with_elo} have ELO scores")
                return True
            else:
                logger.error("Could not verify migration")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying migration: {e}")
            return False

def run_migration():
    """Run the complete migration process"""
    logger.info("=" * 60)
    logger.info("LMSYS ELO Score Column Migration")
    logger.info("=" * 60)
    
    try:
        # Check if column already exists
        if check_column_exists():
            logger.info("✅ elo_score column already exists - migration not needed")
            return True
        
        # Add the column
        success = add_elo_score_column()
        if not success:
            logger.error("❌ Failed to add elo_score column")
            return False
        
        # Verify the migration
        if verify_migration():
            logger.info("✅ Migration completed successfully!")
            logger.info("🎯 Next steps:")
            logger.info("   1. Run the LMSYS ELO data fetcher to populate scores")
            logger.info("   2. Update model prices to assign ELO scores to existing models")
            logger.info("   3. ELO scores will now be included in API responses")
            return True
        else:
            logger.error("❌ Migration verification failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration failed with error: {e}")
        return False

def rollback_migration():
    """Rollback the migration by removing the elo_score column"""
    logger.info("Rolling back ELO score column migration...")
    
    with app_context() as db:
        try:
            if check_column_exists():
                db.session.execute(text("""
                    ALTER TABLE open_router_model 
                    DROP COLUMN elo_score;
                """))
                db.session.commit()
                logger.info("✅ Successfully removed elo_score column")
                return True
            else:
                logger.info("elo_score column does not exist - nothing to rollback")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error rolling back migration: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='LMSYS ELO Score Column Migration')
    parser.add_argument('--rollback', action='store_true', 
                       help='Rollback the migration (remove elo_score column)')
    
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback_migration()
    else:
        success = run_migration()
    
    exit_code = 0 if success else 1
    sys.exit(exit_code)