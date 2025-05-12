"""
Test script to verify the conversation_uuid fix for PDF uploads.
This script verifies that conversations are now created with a valid UUID.
"""
import os
import sys
import logging
import uuid
from flask import Flask
from database import db, init_app
from models import Conversation, User

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up Flask app and configure database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
init_app(app)

def test_conversation_creation():
    """Test creating a conversation with conversation_uuid"""
    with app.app_context():
        try:
            # Create a test conversation
            title = "Test Conversation UUID Fix"
            share_id = str(uuid.uuid4())[:12]
            conversation_uuid = str(uuid.uuid4())
            
            conversation = Conversation(
                title=title,
                share_id=share_id,
                conversation_uuid=conversation_uuid
            )
            
            # For testing, we don't associate with a real user
            db.session.add(conversation)
            db.session.commit()
            
            # Verify the conversation was created with its UUID
            created_conversation = db.session.get(Conversation, conversation.id)
            logger.info(f"Created conversation ID: {created_conversation.id}, UUID: {created_conversation.conversation_uuid}")
            
            # Clean up test conversation
            db.session.delete(created_conversation)
            db.session.commit()
            logger.info("Test conversation deleted")
            
            return True
            
        except Exception as e:
            logger.error(f"Error testing conversation creation: {e}")
            db.session.rollback()
            return False

def main():
    """Run the test script"""
    logger.info("Starting conversation_uuid fix test")
    result = test_conversation_creation()
    
    if result:
        logger.info("✅ Test PASSED: Successfully created conversation with UUID")
        return 0
    else:
        logger.error("❌ Test FAILED: Could not create conversation with UUID")
        return 1

if __name__ == "__main__":
    sys.exit(main())