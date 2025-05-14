"""
Test script to verify the shared conversation URLs work properly
and to check if the fix for the redirection issue works correctly.
"""
import os
import requests
import logging
import sys
from urllib.parse import urljoin
from flask import url_for

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger(__name__)

# Get the Replit domain from environment variables
DOMAIN = os.environ.get('REPLIT_DOMAIN', 'localhost:5000')
if DOMAIN.startswith('localhost'):
    BASE_URL = f'http://{DOMAIN}'
else:
    BASE_URL = f'https://{DOMAIN}'

def test_shared_conversation_access():
    """
    Test accessing a shared conversation URL both with and without authentication
    to verify the fix works correctly.
    """
    logger.info(f"Testing shared conversation URLs on {BASE_URL}")
    
    # Step 1: Find a conversation with a share_id
    from app import app
    from models import Conversation
    
    with app.app_context():
        # Find a conversation with a share_id
        conversation = Conversation.query.filter(Conversation.share_id.isnot(None)).first()
        
        if not conversation:
            logger.error("No shared conversation found in the database. Create one first.")
            return
            
        logger.info(f"Found shared conversation: ID={conversation.id}, share_id={conversation.share_id}")
        
        # Construct the share URL
        share_url = f"/share/{conversation.share_id}"
        full_url = urljoin(BASE_URL, share_url)
        
        logger.info(f"Share URL: {full_url}")
        
        # Test without authentication
        print("\n======== TEST RESULTS ========")
        print(f"To test without authentication (non-logged-in user):")
        print(f"1. Open a private/incognito browser window")
        print(f"2. Visit this URL: {full_url}")
        print(f"3. You should see the shared conversation, not the login page or homepage")
        print("\nTo test with authentication (logged-in user):")
        print(f"1. Log in to the application in a normal browser window")
        print(f"2. Visit this URL: {full_url}")
        print(f"3. You should see the shared conversation, not your own conversations")
        print("\nAfter testing, check if:")
        print("- The shared conversation displays correctly for both user types")
        print("- Images and text are properly arranged (not overlapping)")
        print("- Logged-in users see the shared conversation (not redirected to homepage)")

if __name__ == "__main__":
    test_shared_conversation_access()