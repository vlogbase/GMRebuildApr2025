"""
Migration script to add enable_memory column to the User table
with a default value of True for all existing users.
"""

import logging
import sys
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Boolean
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """
    Run the migration to add the enable_memory column to the User table.
    """
    try:
        # Create a minimal Flask app for this migration
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
        
        db = SQLAlchemy(app)
        
        with app.app_context():
            # Check if column already exists
            conn = db.engine.connect()
            inspector = db.inspect(db.engine)
            columns = [col["name"] for col in inspector.get_columns("user")]
            
            if "enable_memory" in columns:
                logger.info("Column 'enable_memory' already exists in User table")
                return True
            
            logger.info("Adding 'enable_memory' column to User table")
            
            # Create the column with a default value of True
            sql = text("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS enable_memory BOOLEAN DEFAULT true NOT NULL
            """)
            
            conn.execute(sql)
            conn.commit()
            
            logger.info("Column 'enable_memory' successfully added to User table")
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting migration to add enable_memory column")
    success = run_migration()
    
    if success:
        logger.info("Migration completed successfully")
        sys.exit(0)
    else:
        logger.error("Migration failed")
        sys.exit(1)