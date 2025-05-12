"""
Test script to check the application context fixes in the Flask application.
This script simulates the application startup sequence to verify proper context handling.
"""

import os
import logging
import threading
import time
from flask import Flask
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('context_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Create a basic Flask app for testing
class Base(DeclarativeBase):
    pass

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///test.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Create a simple model class for testing
class TestModel(db.Model):
    __tablename__ = 'test_model'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

# Create tables
with app.app_context():
    db.create_all()
    logger.info("Created test database tables")

def background_task():
    """
    Test function to simulate a background task that requires app context
    """
    logger.info("Starting background task...")
    time.sleep(2)  # Simulate short delay
    
    try:
        with app.app_context():
            logger.info("Background task: Creating app context")
            # Try to make a database query
            count = TestModel.query.count()
            logger.info(f"Background task: Found {count} records in test_model table")
            
            # Create a test record if none exist
            if count == 0:
                test_model = TestModel(name="Test Entry")
                db.session.add(test_model)
                db.session.commit()
                logger.info("Background task: Created test record")
        
        logger.info("Background task: Context successfully exited")
    except Exception as e:
        logger.error(f"Error in background task: {e}")
    
    logger.info("Background task completed")

def main():
    """
    Main function to test context creation patterns
    """
    logger.info("Starting application context test")
    
    # Test approach #1: Create thread and check DB inside app context
    with app.app_context():
        logger.info("Main thread: Creating app context")
        try:
            # Check db in main thread
            count = TestModel.query.count()
            logger.info(f"Main thread: Found {count} records in test_model table")
            
            # THIS IS BAD - DON'T START BACKGROUND THREADS WITHIN AN APP CONTEXT
            logger.info("ANTI-PATTERN: Creating background thread inside app context - this can cause issues")
            thread1 = threading.Thread(target=background_task)
            thread1.daemon = True
            thread1.start()
            logger.info("ANTI-PATTERN: Background thread started inside app context")
            
            # Wait for thread to complete
            thread1.join(5)
        except Exception as e:
            logger.error(f"Error in main thread context test 1: {e}")
            
    logger.info("Main thread: App context exited for test 1")
    time.sleep(2)
    
    # Test approach #2: Create thread outside app context (RECOMMENDED)
    logger.info("RECOMMENDED PATTERN: Creating background thread outside app context")
    thread2 = threading.Thread(target=background_task)
    thread2.daemon = True
    thread2.start()
    logger.info("RECOMMENDED PATTERN: Background thread started outside app context")
    
    # Wait for thread to complete
    thread2.join(5)
    
    logger.info("All tests completed. Check logs for detailed results.")
    logger.info("RECOMMENDATION: Always create background threads OUTSIDE any app context")

if __name__ == "__main__":
    main()