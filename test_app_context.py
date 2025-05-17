"""
Simple test to verify that the application context is properly handled
in price_updater.py without running the full initialization process.
"""

import logging
import time
from flask import Flask
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create minimal Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

# Create minimal database model
Base = declarative_base()

class TestModel(Base):
    """Test model to verify database operations within application context"""
    __tablename__ = 'test_app_context'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

# Create database engine and session
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def setup_test_db():
    """Set up the test database"""
    try:
        Base.metadata.create_all(engine)
        logger.info("Test database tables created")
        
        # Add test data
        with app.app_context():
            session = Session()
            
            # Clear existing test data
            session.query(TestModel).delete()
            
            # Add a test record
            test_model = TestModel(
                name="Test App Context",
                created_at=datetime.utcnow() - timedelta(hours=4),
                is_active=True
            )
            session.add(test_model)
            session.commit()
            logger.info("Test data added")
            
        return True
    except Exception as e:
        logger.error(f"Error setting up test database: {e}")
        return False

def test_app_context():
    """Test querying the database with proper application context"""
    try:
        # Function that requires app context
        def get_last_update_time():
            """Get the last update time from the database, requires app context"""
            try:
                with app.app_context():
                    session = Session()
                    last_model = session.query(TestModel).filter(TestModel.is_active == True).order_by(
                        TestModel.created_at.desc()
                    ).first()
                    
                    if last_model and last_model.created_at:
                        last_update_time = last_model.created_at
                        now = datetime.utcnow()
                        hours_since_update = (now - last_update_time).total_seconds() / 3600
                        
                        logger.info(f"Last update was {hours_since_update:.1f} hours ago")
                        return last_update_time, hours_since_update
                    else:
                        logger.info("No records found")
                        return None, 0
            except Exception as e:
                logger.error(f"Error getting last update time: {e}")
                return None, 0
        
        # Test the function
        last_time, hours = get_last_update_time()
        
        if last_time:
            logger.info(f"Successfully retrieved last update time: {last_time}, {hours:.1f} hours ago")
            return True
        else:
            logger.warning("Failed to retrieve last update time")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

def cleanup():
    """Clean up test data"""
    try:
        with app.app_context():
            session = Session()
            session.query(TestModel).delete()
            session.commit()
            logger.info("Test data cleaned up")
        return True
    except Exception as e:
        logger.error(f"Error cleaning up test data: {e}")
        return False

if __name__ == "__main__":
    start_time = time.time()
    
    # Set up test
    if not setup_test_db():
        logger.error("Failed to set up test database")
        exit(1)
    
    # Run test
    success = test_app_context()
    
    # Clean up
    cleanup()
    
    elapsed = time.time() - start_time
    
    if success:
        logger.info(f"Application context test passed in {elapsed:.2f} seconds!")
    else:
        logger.error(f"Application context test failed after {elapsed:.2f} seconds")