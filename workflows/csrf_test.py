"""
Simple script to test CSRF protection in the Flask application.
This validates that CSRF tokens are properly generated and validated.
"""

import sys
import logging
import time
import requests
from pathlib import Path
from flask import Flask, render_template, request, session, jsonify
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to import app
sys.path.append(str(Path(__file__).parent.parent))

def run():
    """
    Test various endpoints for CSRF token inclusion and validation.
    """
    try:
        logger.info("Testing CSRF protection functionality...")
        
        # Import the Flask app
        from app import app
        
        # Check if the app has CSRF protection enabled
        if hasattr(app, 'config') and app.config.get('WTF_CSRF_ENABLED', False):
            logger.info("✓ CSRF protection is enabled in the Flask app")
        else:
            logger.error("✗ CSRF protection is NOT enabled in the Flask app")
        
        # Create a test client
        client = app.test_client()
        
        # Test basic CSRF token generation
        logger.info("Testing CSRF token generation...")
        
        # Get the main page to get a CSRF token
        response = client.get('/')
        
        if response.status_code == 200:
            logger.info("✓ Successfully loaded the main page")
            
            # Get the CSRF token from the meta tag
            html = response.data.decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            
            if csrf_meta and csrf_meta.get('content'):
                csrf_token = csrf_meta.get('content')
                logger.info(f"✓ CSRF token found in meta tag: {csrf_token[:10]}...")
                
                # Now test a POST endpoint that requires CSRF protection
                logger.info("Testing POST request with CSRF token...")
                
                # Try to save a preference with the CSRF token
                preference_data = {
                    'model_id': 'test_model',
                    'is_default': 'true',
                    'csrf_token': csrf_token
                }
                
                headers = {
                    'X-CSRFToken': csrf_token,
                    'Content-Type': 'application/json'
                }
                
                response = client.post('/save_preference', 
                                      json=preference_data,
                                      headers=headers)
                
                if response.status_code == 200 or response.status_code == 401:
                    # 401 is expected if not logged in
                    logger.info(f"✓ POST request with CSRF token succeeded with status {response.status_code}")
                else:
                    logger.error(f"✗ POST request with CSRF token failed with status {response.status_code}")
                
                # Test same endpoint without CSRF token
                logger.info("Testing POST request without CSRF token...")
                bad_data = {'model_id': 'test_model', 'is_default': 'true'}
                response = client.post('/save_preference', json=bad_data)
                
                if response.status_code == 400:
                    logger.info("✓ POST request without CSRF token was correctly rejected with 400 status")
                else:
                    logger.error(f"✗ POST request without CSRF token unexpectedly succeeded with status {response.status_code}")
            else:
                logger.error("✗ CSRF token not found in meta tag")
        else:
            logger.error(f"✗ Failed to load the main page: {response.status_code}")
        
        logger.info("CSRF testing completed")
        
    except Exception as e:
        logger.error(f"Error during CSRF testing: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    run()