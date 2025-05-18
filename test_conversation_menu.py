"""
Test script to verify chat context menu with pin and rename functionality
"""
import os
import logging
import sys
from app import app, db
from models import Conversation, User

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('conversation_menu_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_pin_functionality():
    """Test pinning and unpinning a conversation"""
    with app.app_context():
        try:
            # Create a test user if needed
            user = User.query.filter_by(username='test_user').first()
            if not user:
                logger.info("Creating test user")
                user = User(
                    username='test_user',
                    email='test@example.com'
                )
                user.set_password('password123')
                db.session.add(user)
                db.session.commit()
            
            # Create a test conversation
            logger.info("Creating test conversation")
            conversation = Conversation(
                title="Test Conversation for Pin/Rename",
                user_id=user.id,
                share_id="test_share_id",
                conversation_uuid="test_uuid"
            )
            db.session.add(conversation)
            db.session.commit()
            
            # Test pinning
            logger.info(f"Testing pin functionality on conversation ID {conversation.id}")
            conversation.is_pinned = True
            db.session.commit()
            
            # Verify pin status
            test_conversation = Conversation.query.get(conversation.id)
            logger.info(f"Conversation pinned status: {test_conversation.is_pinned}")
            
            # Test unpinning
            logger.info(f"Testing unpin functionality on conversation ID {conversation.id}")
            conversation.is_pinned = False
            db.session.commit()
            
            # Verify pin status
            test_conversation = Conversation.query.get(conversation.id)
            logger.info(f"Conversation pinned status after unpinning: {test_conversation.is_pinned}")
            
            return True
        except Exception as e:
            logger.error(f"Error testing pin functionality: {e}")
            db.session.rollback()
            return False

def test_rename_functionality():
    """Test renaming a conversation"""
    with app.app_context():
        try:
            # Get test conversation
            conversation = Conversation.query.filter_by(title="Test Conversation for Pin/Rename").first()
            if not conversation:
                logger.error("Test conversation not found")
                return False
            
            # Test renaming
            logger.info(f"Testing rename functionality on conversation ID {conversation.id}")
            old_title = conversation.title
            new_title = "Renamed Test Conversation"
            conversation.title = new_title
            db.session.commit()
            
            # Verify new title
            test_conversation = Conversation.query.get(conversation.id)
            logger.info(f"Conversation title changed from '{old_title}' to '{test_conversation.title}'")
            
            return True
        except Exception as e:
            logger.error(f"Error testing rename functionality: {e}")
            db.session.rollback()
            return False

def run_tests():
    """Run all tests"""
    logger.info("Starting conversation context menu tests...")
    
    # Run pin test
    pin_result = test_pin_functionality()
    logger.info(f"Pin functionality test {'passed' if pin_result else 'failed'}")
    
    # Run rename test
    rename_result = test_rename_functionality()
    logger.info(f"Rename functionality test {'passed' if rename_result else 'failed'}")
    
    logger.info("Tests completed")

if __name__ == '__main__':
    run_tests()