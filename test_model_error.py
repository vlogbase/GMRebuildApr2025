"""
Test script to diagnose HTTP 500 errors when using specific OpenRouter models like Jamba 1.5.

This script sends test requests to the chat endpoint with different models and logs
detailed information about any errors that occur.
"""
import os
import sys
import json
import time
import logging
import requests
import traceback
from datetime import datetime

# Configure logging
log_filename = f'model_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Base URL - use localhost for testing or the actual domain for production
BASE_URL = "http://localhost:5000"
# BASE_URL = "https://gloriamundo.com"  # Uncomment for production testing

# Test config - models to test
TEST_MODELS = [
    "google/gemini-flash-1.5",  # Jamba 1.5
    "anthropic/claude-3-haiku-20240307",  # A reliable model for comparison
    "openai/gpt-4o-2024-05-13"  # Another reliable model for comparison
]

TEST_MESSAGE = "This is a simple test message to verify model functionality."

def get_csrf_token():
    """Get a CSRF token from the main page"""
    try:
        logger.info(f"Getting CSRF token from {BASE_URL}")
        session = requests.Session()
        response = session.get(f"{BASE_URL}/")
        
        if response.status_code != 200:
            logger.error(f"Failed to get main page: {response.status_code}")
            return None
        
        # Extract CSRF token from the HTML response
        import re
        csrf_token_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', response.text)
        if not csrf_token_match:
            logger.error("Could not find CSRF token in the response")
            return None
        
        csrf_token = csrf_token_match.group(1)
        logger.info(f"Found CSRF token: {csrf_token[:10]}...")
        return csrf_token, session
    except Exception as e:
        logger.error(f"Exception getting CSRF token: {e}")
        logger.error(traceback.format_exc())
        return None, None

def test_model(model_id, session, csrf_token):
    """Test a specific model with the chat endpoint"""
    try:
        logger.info(f"Testing model: {model_id}")
        
        headers = {
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token
        }
        
        payload = {
            "message": TEST_MESSAGE,
            "conversation_id": None,  # New conversation each time
            "model": model_id
        }
        
        logger.info(f"Sending request to {BASE_URL}/chat with payload: {json.dumps(payload)}")
        
        # Send the request with streaming disabled to capture full response for error analysis
        response = session.post(
            f"{BASE_URL}/chat",
            headers=headers,
            json=payload,
            stream=False  # Don't stream for error diagnosis
        )
        
        # Log response info
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info(f"Model {model_id} returned 200 OK status - SUCCESS")
            logger.info(f"Response content type: {response.headers.get('Content-Type')}")
            
            # Check if it's a streaming response (event-stream)
            if 'text/event-stream' in response.headers.get('Content-Type', ''):
                logger.info(f"Model {model_id} returned a streaming response")
                # Just log the first few bytes to confirm streaming
                logger.info(f"First bytes of response: {response.content[:200]}")
            else:
                # Log the full response for JSON responses
                try:
                    resp_data = response.json()
                    logger.info(f"Response JSON: {json.dumps(resp_data)[:500]}...")
                except:
                    logger.info(f"Response content: {response.text[:500]}...")
            
            return True
        else:
            # Detailed error logging
            logger.error(f"Model {model_id} failed with status code: {response.status_code}")
            logger.error(f"Response headers: {dict(response.headers)}")
            try:
                logger.error(f"Response content: {response.text[:2000]}...")
            except:
                logger.error(f"Could not get response text. Content: {response.content[:500]}...")
            
            return False
    except Exception as e:
        logger.error(f"Exception testing model {model_id}: {e}")
        logger.error(traceback.format_exc())
        return False

def run_tests():
    """Run tests on all models in the test config"""
    result = get_csrf_token()
    if not result:
        logger.error("Could not get CSRF token, aborting tests")
        return
    
    csrf_token, session = result
    
    # Test each model and collect results
    results = {}
    
    for model_id in TEST_MODELS:
        logger.info(f"=== Starting test for model: {model_id} ===")
        success = test_model(model_id, session, csrf_token)
        results[model_id] = "SUCCESS" if success else "FAILED"
        logger.info(f"=== Completed test for model: {model_id} - {results[model_id]} ===")
        time.sleep(1)  # Brief pause between tests
    
    # Print summary
    logger.info("=== Test Results Summary ===")
    for model_id, result in results.items():
        logger.info(f"Model {model_id}: {result}")
    logger.info(f"Log file: {log_filename}")

if __name__ == "__main__":
    logger.info("Starting model error diagnosis tests")
    run_tests()
    logger.info("Completed model error diagnosis tests")