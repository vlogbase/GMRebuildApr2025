"""
Identify why share URLs redirect to homepage in production
"""
import sys
import logging
from urllib.parse import urlparse
from app import app, db, logger
from models import Conversation
from werkzeug.test import Client
from werkzeug.wrappers import Response

# Configure detailed logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)

def test_link_structure():
    """Test the structure of shared links"""
    with app.app_context():
        # Get a share_id from the database
        conversation = Conversation.query.filter(Conversation.share_id.isnot(None)).first()
        if not conversation:
            logger.error("No shared conversations found in database")
            return
            
        # Get the share URL structure
        share_url = f"/share/{conversation.share_id}"
        logger.info(f"Share URL structure: {share_url}")
        
        # Test what happens when we access it
        client = Client(app, Response)
        response = client.get(share_url)
        
        logger.info(f"Response code: {response.status_code}")
        if 300 <= response.status_code < 400:
            logger.info(f"Redirect location: {response.headers.get('Location')}")
            
            # Parse the redirect location
            redirect_url = response.headers.get('Location')
            parsed = urlparse(redirect_url)
            logger.info(f"Redirect path: {parsed.path}")
            logger.info(f"Redirect query: {parsed.query}")
            
        # Compare with JavaScript URL construction
        origin = "https://example.com"
        client_url = f"{origin}{share_url}"
        logger.info(f"URL constructed by JavaScript: {client_url}")
        
        # Check if user agent might be affecting the response
        # Try with different user agents
        user_agents = {
            "Chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Firefox": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mobile": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        }
        
        for name, agent in user_agents.items():
            logger.info(f"Testing with {name} user agent")
            headers = {"User-Agent": agent}
            ua_response = client.get(share_url, headers=headers)
            logger.info(f"Response code: {ua_response.status_code}")
            if 300 <= ua_response.status_code < 400:
                logger.info(f"Redirect location: {ua_response.headers.get('Location')}")
        
        # Log success or failure
        if response.status_code == 200:
            logger.info("Share URL works correctly in test environment")
        else:
            logger.error("Share URL is NOT working correctly in test environment")
            
def examine_view_shared_conversation():
    """Examine the view_shared_conversation function call"""
    with app.app_context():
        from app import view_shared_conversation
        
        # Get a share_id from the database
        conversation = Conversation.query.filter(Conversation.share_id.isnot(None)).first()
        if not conversation:
            logger.error("No shared conversations found in database")
            return
            
        # Get function info
        logger.info(f"Function name: {view_shared_conversation.__name__}")
        logger.info(f"Function module: {view_shared_conversation.__module__}")
        logger.info(f"Function docstring: {view_shared_conversation.__doc__}")
        
        # Direct test of shared URL routing
        client = Client(app, Response)
        response = client.get(f"/share/{conversation.share_id}")
        
        # Check if flashing messages affects the redirect
        if hasattr(response, 'flashes'):
            flash_messages = response.flashes
            logger.info(f"Flash messages: {flash_messages}")
        
        # Log all routes to see if there are conflicting ones
        logger.info("All app routes:")
        for rule in app.url_map.iter_rules():
            logger.info(f"Route: {rule.rule}, Endpoint: {rule.endpoint}")
        
        # Log the specific response template info
        if response.status_code == 200:
            logger.info("Route correctly served the shared conversation")
            # We would log template context if we could access it
        else:
            logger.error(f"Route is not working correctly: Status {response.status_code}")

if __name__ == "__main__":
    logger.info("Starting share link debug diagnostics")
    test_link_structure()
    examine_view_shared_conversation()
    logger.info("Completed share link debug diagnostics")