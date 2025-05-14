"""
Script to check how JavaScript might be constructing the URLs.
"""
import logging
import re
from app import app, db
from models import Conversation
from urllib.parse import urlparse, urljoin

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_js_url_construction():
    """Check how JavaScript constructs URLs"""
    with app.app_context():
        # Find a shared conversation
        conversation = Conversation.query.filter(Conversation.share_id.isnot(None)).first()
        if not conversation:
            logger.error("No shared conversation found in database")
            return
            
        # Find the JavaScript file with the share function
        js_file_path = "static/js/script.js"
        try:
            with open(js_file_path, 'r') as f:
                js_content = f.read()
        except Exception as e:
            logger.error(f"Error reading JavaScript file: {e}")
            return
            
        # Extract how the shareUrl is constructed
        share_url_pattern = r"const\s+shareUrl\s*=\s*([^;]+);"
        match = re.search(share_url_pattern, js_content)
        if match:
            js_construction = match.group(1)
            logger.info(f"JavaScript constructs share URL as: {js_construction}")
            
            # Check how window.location.origin would be formatted
            logger.info("Possible window.location.origin values:")
            logger.info("  In development: http://localhost:5000")
            logger.info("  In production: https://gloriamundo.repl.co")
            
            # Simulate what the JavaScript would construct in different environments
            share_path = f"/share/{conversation.share_id}"
            dev_origin = "http://localhost:5000"
            prod_origin = "https://gloriamundo.repl.co"
            
            dev_url = dev_origin + share_path
            prod_url = prod_origin + share_path
            
            logger.info(f"In development, URL would be: {dev_url}")
            logger.info(f"In production, URL would be: {prod_url}")
            
            # Parse the URLs to check components
            parsed_dev = urlparse(dev_url)
            parsed_prod = urlparse(prod_url)
            
            logger.info(f"Development URL path: {parsed_dev.path}")
            logger.info(f"Production URL path: {parsed_prod.path}")
            
            # Suggest potential issues
            logger.info("\nPotential issues:")
            logger.info("1. Ensure the domain is properly configured in the project")
            logger.info("2. Check if there's a URL prefix added in production")
            logger.info("3. Verify that the front-end JavaScript is using the correct origin")
            logger.info("4. Check if CORS or CSP policies might be affecting the URLs")
            
            # Look for relative URL usages
            if "window.location.origin +" in js_content:
                logger.info("Found absolute URL construction using window.location.origin")
            if "data.share_url" in js_content:
                logger.info("Found usage of data.share_url from server response")
                
            # Check the Flask URL generation
            with app.test_request_context():
                from flask import url_for
                flask_url = url_for('view_shared_conversation', share_id=conversation.share_id)
                logger.info(f"Flask generates URL as: {flask_url}")
                
                # Compare with front-end construction
                logger.info(f"If JavaScript appends this to origin, result would be: {dev_origin}{flask_url}")
        else:
            logger.error("Couldn't find share URL construction in JavaScript")
            
if __name__ == "__main__":
    check_js_url_construction()