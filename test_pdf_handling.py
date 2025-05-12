"""
Test script to verify PDF handling functionality with proper app context.

This script tests:
1. Database schema has correct PDF fields on Message model
2. App context is properly handled during database operations
3. PDF URLs can be saved to the database
"""
import base64
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pdf_test.log')
    ]
)

logger = logging.getLogger(__name__)

# Import our app context handler
try:
    from ensure_app_context import ensure_app_context
    logger.info("Successfully imported ensure_app_context")
except ImportError as e:
    logger.error(f"Error importing ensure_app_context: {e}")
    sys.exit(1)

def test_message_model():
    """Test that the Message model has the required PDF fields"""
    try:
        from models import Message
        logger.info("Successfully imported Message model")
        
        # Create a test message instance to verify fields
        test_message = Message()
        
        # Check for pdf_url field
        if hasattr(test_message, 'pdf_url'):
            logger.info("✅ Message model has pdf_url field")
        else:
            logger.error("❌ Message model missing pdf_url field")
            return False
            
        # Check for pdf_filename field
        if hasattr(test_message, 'pdf_filename'):
            logger.info("✅ Message model has pdf_filename field")
        else:
            logger.error("❌ Message model missing pdf_filename field")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error testing Message model: {e}")
        return False

def test_db_connection():
    """Test database connection with app context"""
    try:
        with ensure_app_context():
            from app import db
            # Simple query to test connection
            result = db.session.execute("SELECT 1").scalar()
            if result == 1:
                logger.info("✅ Database connection successful with app context")
                return True
            else:
                logger.error("❌ Database connection failed")
                return False
    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
        return False

def test_save_pdf_message():
    """Test saving a message with PDF data to the database"""
    try:
        # Generate a sample base64 PDF data (just a placeholder)
        sample_pdf_data = f"data:application/pdf;base64,{base64.b64encode(b'Test PDF content').decode('utf-8')}"
        
        with ensure_app_context():
            from app import db
            from models import Message, Conversation
            
            # First, create a test conversation if needed
            conversation = db.session.query(Conversation).filter_by(title="PDF Test Conversation").first()
            if not conversation:
                conversation = Conversation(
                    title="PDF Test Conversation",
                    created_at=datetime.utcnow(),
                    user_id=1  # Using ID 1 for testing
                )
                db.session.add(conversation)
                db.session.commit()
                logger.info(f"Created test conversation with ID: {conversation.id}")
            
            # Create a test message with PDF data
            message = Message(
                conversation_id=conversation.id,
                role="user",
                content="Test message with PDF attachment",
                created_at=datetime.utcnow(),
                pdf_url=sample_pdf_data,
                pdf_filename="test_document.pdf"
            )
            
            db.session.add(message)
            db.session.commit()
            
            logger.info(f"✅ Successfully saved PDF message with ID: {message.id}")
            
            # Verify we can read it back
            saved_message = db.session.query(Message).get(message.id)
            if saved_message and saved_message.pdf_url == sample_pdf_data:
                logger.info("✅ Successfully retrieved PDF message from database")
                return True
            else:
                logger.error("❌ Failed to properly retrieve PDF message")
                return False
                
    except Exception as e:
        logger.error(f"Error testing PDF message saving: {e}")
        return False

def run_tests():
    """Run all PDF handling tests"""
    logger.info("Starting PDF handling tests...")
    
    # Track test results
    test_results = {
        "message_model": False,
        "db_connection": False,
        "save_pdf_message": False
    }
    
    # Run tests
    test_results["message_model"] = test_message_model()
    test_results["db_connection"] = test_db_connection()
    if test_results["message_model"] and test_results["db_connection"]:
        test_results["save_pdf_message"] = test_save_pdf_message()
    
    # Print summary
    logger.info("=== PDF Handling Test Results ===")
    for test, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test}: {status}")
    
    # Overall result
    if all(test_results.values()):
        logger.info("🎉 All PDF handling tests passed! The app should handle PDFs correctly.")
        return True
    else:
        logger.error("⚠️ Some PDF handling tests failed.")
        return False

if __name__ == "__main__":
    run_tests()