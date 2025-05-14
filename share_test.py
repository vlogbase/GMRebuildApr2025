"""
Script to test share links
"""
import logging
from app import app, db
from models import Conversation

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_share_url():
    """Test share URL generation and access"""
    with app.app_context():
        # Get a conversation with a share ID
        conversation = Conversation.query.filter(Conversation.share_id.isnot(None)).first()
        
        if not conversation:
            logger.error("No conversation with share_id found in database")
            return
        
        # Print conversation details
        logger.info(f"Test conversation: id={conversation.id}, share_id={conversation.share_id}, title={conversation.title}")
        
        # Generate the share URL
        # Can't use url_for outside request context, so construct manually
        share_url = f"/share/{conversation.share_id}"
        logger.info(f"Share URL: {share_url}")
        
        # Simulate the share_conversation endpoint response
        logger.info("Simulating share_conversation endpoint response")
        conversation_share_url = f"/share/{conversation.share_id}"
        logger.info(f"Generated share URL path: {conversation_share_url}")
        
        # Print how a client would construct the full URL
        full_url = f"https://example.com{conversation_share_url}"
        logger.info(f"Full URL a client would construct: {full_url}")
        
        logger.info("Test complete")

if __name__ == "__main__":
    test_share_url()