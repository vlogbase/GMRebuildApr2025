"""
Debug script to test the behavior of the shared conversation route
with authenticated and non-authenticated users.
"""
import logging
import sys
from flask import session, url_for
from flask_login import current_user, login_user, logout_user
from app import app, db
from models import User, Conversation, Message

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger(__name__)

def check_shared_link_redirection():
    """Test the view_shared_conversation route's behavior with authenticated and non-authenticated users"""
    # First, find a conversation with a share_id
    with app.app_context():
        try:
            # Find a shared conversation
            shared_conversation = Conversation.query.filter(Conversation.share_id.isnot(None)).first()
            
            if not shared_conversation:
                logger.error("No shared conversations found in the database")
                return
                
            logger.info(f"Found shared conversation with ID: {shared_conversation.id} and share_id: {shared_conversation.share_id}")
            
            # Get the owner user if user_id exists
            owner = None
            if shared_conversation.user_id:
                owner = User.query.get(shared_conversation.user_id)
                if owner:
                    logger.info(f"Conversation owner: {owner.username} (ID: {owner.id})")
                else:
                    logger.warning(f"Owner user (ID: {shared_conversation.user_id}) not found but will continue testing")
            else:
                logger.warning("Conversation has NULL user_id - this could cause redirection issues")
            
            # Generate the share URL
            share_url = url_for('view_shared_conversation', share_id=shared_conversation.share_id)
            logger.info(f"Share URL: {share_url}")
            
            # Create a test client
            client = app.test_client()
            
            # Test 1: Access as non-authenticated user
            with client:
                logger.info("TEST 1: Accessing share link as non-authenticated user")
                response = client.get(share_url)
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Response location header: {response.headers.get('Location', 'No redirect')}")
                if response.status_code == 302:
                    logger.info(f"Redirected to: {response.headers.get('Location')}")
                
                # Check if we got the shared_conversation template or index template
                if b'shared-container' in response.data:
                    logger.info("Rendered shared_conversation.html template")
                elif b'chat-container' in response.data:
                    logger.info("Rendered index.html template")
                else:
                    logger.info("Unknown template rendered")
            
            # Test 2: Access as authenticated user (any user)
            # Find any user in the system
            other_user = User.query.first()
            if not other_user:
                logger.warning("No user found for testing authenticated access")
                return
                
            with client:
                logger.info(f"TEST 2: Accessing share link as authenticated user (ID: {other_user.id})")
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(other_user.id)
                    
                response = client.get(share_url)
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Response location header: {response.headers.get('Location', 'No redirect')}")
                if response.status_code == 302:
                    logger.info(f"Redirected to: {response.headers.get('Location')}")
                
                # Check if we got the shared_conversation template or index template
                if b'shared-container' in response.data:
                    logger.info("Rendered shared_conversation.html template")
                elif b'chat-container' in response.data:
                    logger.info("Rendered index.html template")
                else:
                    logger.info("Unknown template rendered")
            
            # Test 3: Access as conversation owner
            with client:
                logger.info(f"TEST 3: Accessing share link as conversation owner (ID: {owner.id})")
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(owner.id)
                    
                response = client.get(share_url)
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Response location header: {response.headers.get('Location', 'No redirect')}")
                if response.status_code == 302:
                    logger.info(f"Redirected to: {response.headers.get('Location')}")
                
                # Check if we got the shared_conversation template or index template
                if b'shared-container' in response.data:
                    logger.info("Rendered shared_conversation.html template")
                elif b'chat-container' in response.data:
                    logger.info("Rendered index.html template")
                else:
                    logger.info("Unknown template rendered")
                    
        except Exception as e:
            logger.exception(f"Error during debugging: {e}")

if __name__ == "__main__":
    check_shared_link_redirection()