"""
Script to debug the shared conversation route
"""
import logging
import os
from flask import url_for
from app import app, db, logger
from werkzeug.test import Client
from werkzeug.wrappers import Response

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def debug_shared_route():
    """Test the shared conversation route with direct requests"""
    with app.app_context():
        # Find a conversation with a shared ID in the database
        from models import Conversation
        shared_conversation = Conversation.query.filter(Conversation.share_id.isnot(None)).first()
        
        if not shared_conversation:
            logger.error("No conversation with share_id found")
            return
            
        logger.info(f"Found conversation with ID {shared_conversation.id} and share_id {shared_conversation.share_id}")
        
        # Create a test client
        client = Client(app, Response)
        
        # Make a request to the shared conversation route
        share_url = f"/share/{shared_conversation.share_id}"
        logger.info(f"Testing share URL: {share_url}")
        
        # Make the request
        response = client.get(share_url)
        
        # Log the response
        logger.info(f"Response status: {response.status}")
        logger.info(f"Response headers: {response.headers}")
        
        # Check for redirects
        if 300 <= response.status_code < 400:
            logger.warning(f"Redirected to: {response.headers.get('Location')}")
            
        # Log the first 500 characters of the response
        body = response.get_data(as_text=True)
        logger.info(f"Response body (first 500 chars): {body[:500]}")
        
        # Check for specific patterns in the response
        if "The shared conversation link is invalid or has expired" in body:
            logger.error("Found error message: 'The shared conversation link is invalid or has expired'")
        
        if "<title>Shared Conversation" in body:
            logger.info("Found expected title for shared conversation page")
            
        # Now test with an invalid share_id
        invalid_share_url = "/share/invalid_share_id"
        logger.info(f"Testing invalid share URL: {invalid_share_url}")
        
        invalid_response = client.get(invalid_share_url)
        logger.info(f"Invalid response status: {invalid_response.status}")
        
        if 300 <= invalid_response.status_code < 400:
            logger.warning(f"Invalid share redirected to: {invalid_response.headers.get('Location')}")

if __name__ == "__main__":
    debug_shared_route()