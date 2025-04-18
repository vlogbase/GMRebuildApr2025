"""
A simple test script to check image formats compatible with Gemini models.
"""

import os
import requests
import json
import logging
from urllib.parse import urlparse
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key
api_key = os.environ.get('OPENROUTER_API_KEY')
if not api_key:
    raise ValueError("OPENROUTER_API_KEY environment variable not set")

# Test URLs
test_urls = [
    "https://picsum.photos/id/237/300/200.jpg",  # Simple JPEG image
    "https://picsum.photos/300/200?random=1",    # URL with query parameters
]

# Test function
def test_image_url(model, image_url):
    """Test an image URL with a specific model"""
    logger.info(f"Testing {model} with image URL: {image_url}")
    
    # Parse URL components for logging
    parsed_url = urlparse(image_url)
    domain = parsed_url.netloc
    path = parsed_url.path
    extension = os.path.splitext(path)[1].lower()
    has_query = bool(parsed_url.query)
    
    logger.info(f"URL domain: {domain}")
    logger.info(f"URL path: {path}")
    logger.info(f"URL extension: {extension or 'none'}")
    logger.info(f"Has query parameters: {has_query}")
    
    # Create multimodal content
    multimodal_content = [
        {"type": "text", "text": "What's in this image?"},
        {"type": "image_url", "image_url": {"url": image_url}}
    ]
    
    # Create request payload
    payload = {
        'model': model,
        'messages': [
            {
                "role": "user",
                "content": multimodal_content
            }
        ],
        'max_tokens': 300,
        'stream': False
    }
    
    # Create headers
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:5000'
    }
    
    # Make the request
    try:
        logger.info("Sending request to OpenRouter API...")
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Log success
        response_json = response.json()
        model_used = response_json.get('model', 'unknown')
        content = response_json['choices'][0]['message']['content']
        
        logger.info(f"Success with model: {model_used}")
        logger.info(f"Response: {content[:150]}...")
        return True, content
        
    except Exception as e:
        logger.error(f"Error: {e}")
        if 'response' in locals():
            logger.error(f"Response status: {response.status_code}")
            logger.error(f"Response text: {response.text}")
        return False, str(e)

# Main test function
def main():
    # Models to test
    models = [
        "google/gemini-2.5-pro-preview-03-25",  # Gemini model
        "openai/gpt-4o"                        # GPT-4o for comparison
    ]
    
    results = {}
    
    # Test each model with each URL
    for model in models:
        model_results = {}
        for url in test_urls:
            logger.info(f"\n--- Testing {model} with {url} ---\n")
            success, response = test_image_url(model, url)
            model_results[url] = {"success": success, "response": response}
        results[model] = model_results
    
    # Print summary
    logger.info("\n\n=== TEST RESULTS SUMMARY ===\n")
    for model, urls in results.items():
        logger.info(f"Model: {model}")
        for url, result in urls.items():
            status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
            logger.info(f"  {status} - {url}")
    
    return results

if __name__ == "__main__":
    main()