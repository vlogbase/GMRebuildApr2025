"""
Test script to verify the chat endpoint is working properly after the fix.
This script sends a POST request to the /chat endpoint with the required CSRF token.
"""
import requests
import json
import logging
import sys
import re

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def test_chat_endpoint():
    # Base URL - use localhost for testing
    base_url = "http://localhost:5000"
    
    # Step 1: Get CSRF token from main page
    session = requests.Session()
    response = session.get(f"{base_url}/")
    
    if response.status_code != 200:
        logger.error(f"Failed to get main page: {response.status_code}")
        return False
    
    # Extract CSRF token from the HTML response - look for meta tag
    csrf_token_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', response.text)
    if not csrf_token_match:
        logger.error("Could not find CSRF token in the response")
        return False
    
    csrf_token = csrf_token_match.group(1)
    logger.info(f"Found CSRF token: {csrf_token[:10]}...")
    
    # Step 2: Send a chat message
    headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token
    }
    
    # Build a simple chat message payload
    payload = {
        "message": "Hello, this is a test message",
        "conversation_id": None,  # New conversation
        "model_id": "openai/gpt-3.5-turbo"  # Use a standard model
    }
    
    # Send the request
    try:
        response = session.post(
            f"{base_url}/chat",
            headers=headers,
            json=payload,
            stream=True  # Important: chat endpoint uses streaming
        )
        
        # Check status code
        if response.status_code == 200:
            logger.info("Chat endpoint returned 200 status - PASS!")
            # Read some of the streaming response
            for line in response.iter_lines():
                if line:
                    logger.info(f"Received chunk: {line.decode('utf-8')[:100]}...")
                    break  # Just read the first chunk to confirm streaming works
            return True
        else:
            logger.error(f"Chat endpoint failed with status code: {response.status_code}")
            logger.error(f"Response content: {response.text[:500]}")
            return False
    
    except Exception as e:
        logger.error(f"Exception during chat request: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Testing chat endpoint with CSRF token...")
    success = test_chat_endpoint()
    
    if success:
        logger.info("✅ TEST PASSED: Chat endpoint is working correctly with CSRF token")
        sys.exit(0)
    else:
        logger.error("❌ TEST FAILED: Chat endpoint is not working correctly")
        sys.exit(1)