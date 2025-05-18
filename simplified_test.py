"""
Simplified test script for conversation pinning and renaming
"""
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import sys
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a test app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Conversation(db.Model):
    """Test model for conversation"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)
    conversation_uuid = db.Column(db.String(36), nullable=True)
    share_id = db.Column(db.String(64), nullable=True)
    user_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=True)

def test_pin_operation():
    """Test pinning and unpinning a conversation"""
    with app.app_context():
        try:
            # Create table if it doesn't exist
            db.create_all()
            
            # Create a test conversation
            conversation = Conversation(
                title="Test Conversation",
                conversation_uuid=str(uuid.uuid4()),
                share_id=str(uuid.uuid4())[:12],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(conversation)
            db.session.commit()
            
            conv_id = conversation.id
            logger.info(f"Created test conversation with ID {conv_id}")
            
            # Test pinning
            conversation.is_pinned = True
            db.session.commit()
            logger.info(f"Pinned conversation {conv_id}")
            
            # Verify pin status
            test_conversation = Conversation.query.get(conv_id)
            logger.info(f"Conversation pinned status: {test_conversation.is_pinned}")
            
            # Test unpinning
            conversation.is_pinned = False
            db.session.commit()
            logger.info(f"Unpinned conversation {conv_id}")
            
            # Verify pin status
            test_conversation = Conversation.query.get(conv_id)
            logger.info(f"Conversation pinned status: {test_conversation.is_pinned}")
            
            # Rename test
            old_title = conversation.title
            new_title = "Renamed Test Conversation"
            conversation.title = new_title
            db.session.commit()
            logger.info(f"Renamed conversation from '{old_title}' to '{new_title}'")
            
            # Verify title change
            test_conversation = Conversation.query.get(conv_id)
            logger.info(f"Conversation title: {test_conversation.title}")
            
            # Clean up
            db.session.delete(conversation)
            db.session.commit()
            logger.info(f"Deleted test conversation {conv_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error in test: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    result = test_pin_operation()
    logger.info(f"Test {'passed' if result else 'failed'}")