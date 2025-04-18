"""
Test script for OpenRouter's unified multimodal API.
This script tests sending the same image to different multimodal models
using the standardized OpenRouter format.
"""
import os
import sys
import json
import requests
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get OpenRouter API key from environment
API_KEY = os.environ.get('OPENROUTER_API_KEY')
if not API_KEY:
    logger.error("OPENROUTER_API_KEY not found in environment variables")
    sys.exit(1)

# Get test image URL
TEST_IMAGE_URL = os.environ.get('TEST_IMAGE_URL')
if not TEST_IMAGE_URL:
    logger.error("TEST_IMAGE_URL not found in environment variables. Set this to a valid image URL.")
    # We'll generate a test image URL by running the upload test
    logger.info("Generating a test image URL by running mini_test.py...")
    try:
        import mini_test
        # The mini_test script prints the image URL at the end
        # We can parse its output to get the URL
        logger.info("mini_test.py completed. Check the output for the image URL.")
        logger.info("Please set the TEST_IMAGE_URL environment variable and try again.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running mini_test.py: {e}")
        sys.exit(1)

# Models to test - using two models to verify cross-model compatibility
TEST_MODELS = [
    "google/gemini-flash-1.5",  # Gemini model
    "anthropic/claude-3-opus-20240229"  # Claude model
]

# Test prompt
TEST_PROMPT = "Describe this image in detail. What do you see?"

def test_model(model_id, image_url):
    """Test a specific model with the given image URL"""
    logger.info(f"Testing model: {model_id}")
    
    # Prepare headers
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:5000'  # Adjust if needed
    }
    
    # Prepare payload with OpenRouter's unified format for multimodal
    payload = {
        'model': model_id,
        'messages': [
            {
                'role': 'user', 
                'content': [
                    {'type': 'text', 'text': TEST_PROMPT},
                    {'type': 'image_url', 'image_url': {'url': image_url}}
                ]
            }
        ],
        'stream': False  # Don't stream for easier response handling
    }
    
    # Log the payload being sent
    logger.info(f"Sending payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Send request to OpenRouter
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=60.0  # Longer timeout for more complex models like Claude
        )
        
        # Check if request was successful
        if response.status_code == 200:
            result = response.json()
            
            # Extract and print the model's response
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                logger.info(f"Response from {model_id}:\n{content[:500]}...")
                logger.info(f"Full response length: {len(content)} characters")
                return True, content
            else:
                logger.error(f"No choices in response: {result}")
                return False, None
        else:
            logger.error(f"Error from OpenRouter API: {response.status_code} - {response.text}")
            return False, None
            
    except Exception as e:
        logger.error(f"Error testing model {model_id}: {e}")
        return False, None

def run_tests():
    """Run tests on all specified models"""
    logger.info(f"Starting multimodal tests with image URL: {TEST_IMAGE_URL}")
    
    results = {}
    
    for model in TEST_MODELS:
        success, content = test_model(model, TEST_IMAGE_URL)
        results[model] = {
            'success': success,
            'content_sample': content[:200] + "..." if content else None
        }
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("="*80)
    
    for model, result in results.items():
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        logger.info(f"{status} - {model}")
        if result['content_sample']:
            logger.info(f"Sample response: {result['content_sample']}")
        logger.info("-"*80)

if __name__ == "__main__":
    run_tests()