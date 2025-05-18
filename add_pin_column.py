"""
Simple script to add the is_pinned column to the Conversation table using execute_sql_tool
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create simple app with database connection
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def add_pin_column():
    """Add is_pinned column to conversation table"""
    with app.app_context():
        try:
            # Check if column exists
            result = db.session.execute("SELECT column_name FROM information_schema.columns WHERE table_name='conversation' AND column_name='is_pinned'")
            column_exists = bool(result.scalar())
            
            if not column_exists:
                # Add the column if it doesn't exist
                db.session.execute("ALTER TABLE conversation ADD COLUMN is_pinned BOOLEAN DEFAULT FALSE")
                db.session.commit()
                logger.info("Added is_pinned column to conversation table")
                return True
            else:
                logger.info("is_pinned column already exists")
                return True
        except Exception as e:
            logger.error(f"Error adding column: {e}")
            return False

if __name__ == "__main__":
    result = add_pin_column()
    logger.info(f"Operation {'successful' if result else 'failed'}")