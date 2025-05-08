"""
Migration script to add model_is_active field to OpenRouterModel
and user_is_active field to User model
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import Column, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database engine
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    logger.error("DATABASE_URL environment variable not set")
    sys.exit(1)

engine = create_engine(database_url)
Base = declarative_base()
Session = sessionmaker(bind=engine)

def execute_with_error_handling(session, statement, params=None):
    """Execute SQL with error handling for migrations"""
    try:
        if params:
            session.execute(statement, params)
        else:
            session.execute(statement)
        return True
    except (OperationalError, ProgrammingError) as e:
        if "already exists" in str(e):
            logger.info(f"Column already exists: {e}")
            return True
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def run_migrations():
    """Run all migrations for model_is_active field"""
    session = Session()
    
    try:
        logger.info("Starting migrations for model activity status fields")
        
        # Check if OpenRouterModel table exists
        try:
            result = session.execute(text("SELECT 1 FROM open_router_model LIMIT 1"))
            open_router_model_exists = True
            logger.info("OpenRouterModel table exists")
        except Exception:
            open_router_model_exists = False
            logger.info("OpenRouterModel table does not exist yet")
        
        # Add model_is_active column to OpenRouterModel if the table exists
        if open_router_model_exists:
            add_column_sql = text("""
                ALTER TABLE open_router_model 
                ADD COLUMN IF NOT EXISTS model_is_active BOOLEAN NOT NULL DEFAULT true
            """)
            
            if execute_with_error_handling(session, add_column_sql):
                logger.info("Added model_is_active column to OpenRouterModel")
            else:
                logger.error("Failed to add model_is_active column to OpenRouterModel")
        
        # Check if User table exists 
        try:
            result = session.execute(text("SELECT 1 FROM user LIMIT 1"))
            user_table_exists = True
            logger.info("User table exists")
        except Exception:
            user_table_exists = False
            logger.info("User table does not exist yet")
            
        # Add user_is_active column to User if the table exists
        if user_table_exists:
            check_column_sql = text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='user' AND column_name='is_active'
            """)
            
            result = session.execute(check_column_sql).fetchone()
            
            if result:
                # Rename the existing is_active column to user_is_active
                rename_column_sql = text("""
                    ALTER TABLE "user" 
                    RENAME COLUMN is_active TO user_is_active
                """)
                
                if execute_with_error_handling(session, rename_column_sql):
                    logger.info("Renamed is_active column to user_is_active in User table")
                else:
                    logger.error("Failed to rename is_active column in User table")
            else:
                # Check if user_is_active column already exists
                check_new_column_sql = text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='user' AND column_name='user_is_active'
                """)
                
                result = session.execute(check_new_column_sql).fetchone()
                
                if not result:
                    add_column_sql = text("""
                        ALTER TABLE "user" 
                        ADD COLUMN IF NOT EXISTS user_is_active BOOLEAN NOT NULL DEFAULT true
                    """)
                    
                    if execute_with_error_handling(session, add_column_sql):
                        logger.info("Added user_is_active column to User table")
                    else:
                        logger.error("Failed to add user_is_active column to User table")
                else:
                    logger.info("user_is_active column already exists in User table")
        
        # Commit the transaction
        session.commit()
        logger.info("Migrations completed successfully")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Migration failed: {e}")
        return False
    
    finally:
        session.close()

if __name__ == "__main__":
    run_migrations()