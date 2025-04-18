"""
Test script specifically for Gemini models to diagnose image URL issues.

This script tests different image URL formats with Gemini models through OpenRouter
to identify what types of image URLs work best with Gemini.
"""

import os
import requests
import json
import time
import logging
import urllib.parse
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key
api_key = os.environ.get('OPENROUTER_API_KEY')
if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found in environment variables")

# Gemini models to test
GEMINI_MODELS = [
    "google/gemini-2.5-pro-preview-03-25",
    "google/gemini-2.0-flash-exp:free"
]

# Test image URLs - include several types:
# 1. Public plain HTTP URLs without query params
# 2. URLs with query parameters
# 3. Azure Blob Storage URLs with SAS tokens
# 4. Different file formats (JPG, PNG, WEBP)
IMAGE_URLS = [
    # Public images from a CDN
    "https://picsum.photos/id/237/300/200.jpg",  # Simple JPG from picsum
    "https://picsum.photos/id/237/300/200",  # No file extension
    
    # Image with query parameters
    "https://picsum.photos/300/200?random=1",  # URL with query parameters
    
    # Different file formats
    "https://fastly.picsum.photos/id/866/300/200.jpg",
    "https://fastly.picsum.photos/id/237/300/200.png",
    
    # Images from our static directory (if they exist)
    "http://localhost:5000/static/sample_image.jpg",
]

def create_clean_url(image_url):
    """
    Convert an existing URL (potentially with SAS tokens or query parameters)
    into a clean URL without query parameters. This can make the URL more compatible
    with certain models.
    
    Args:
        image_url (str): The original image URL
        
    Returns:
        str: A clean version of the URL without query parameters
    """
    # Parse the URL
    parsed_url = urllib.parse.urlparse(image_url)
    
    # Remove query parameters and fragment
    clean_url = urllib.parse.urlunparse(
        (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", "")
    )
    
    logger.info(f"Original URL: {image_url[:100]}...")
    logger.info(f"Clean URL: {clean_url}")
    
    return clean_url

def test_gemini_with_image(model_id, image_url, prompt_text="What's in this image?"):
    """
    Test a Gemini model with an image URL and detailed logging.
    
    Args:
        model_id (str): The OpenRouter model ID for Gemini
        image_url (str): The image URL to test
        prompt_text (str): The prompt text to send with the image
        
    Returns:
        dict: The response from the API
    """
    # Analyze the URL
    parsed_url = urllib.parse.urlparse(image_url)
    domain = parsed_url.netloc
    path = parsed_url.path
    extension = os.path.splitext(path)[1].lower()
    has_query_params = bool(parsed_url.query)
    
    logger.info(f"Testing Gemini model: {model_id}")
    logger.info(f"  Image URL: {image_url[:100]}...")
    logger.info(f"  Domain: {domain}")
    logger.info(f"  Path: {path}")
    logger.info(f"  Extension: {extension or 'none'}")
    logger.info(f"  Has query parameters: {has_query_params}")
    
    # Prepare the request
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:5000'
    }
    
    # OpenRouter's unified multimodal format
    multimodal_content = [
        {"type": "text", "text": prompt_text},
        {"type": "image_url", "image_url": {"url": image_url}}
    ]
    
    payload = {
        'model': model_id,
        'messages': [
            {
                "role": "user",
                "content": multimodal_content
            }
        ],
        'max_tokens': 300,
        'stream': False,
        'temperature': 0.7
    }
    
    try:
        logger.info(f"Sending request to OpenRouter...")
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=60
        )
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Log response
        response_json = response.json()
        content = response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
        model_used = response_json.get('model', 'unknown')
        
        logger.info(f"✅ Success with Gemini model: {model_used}")
        logger.info(f"Response (first 150 chars): {content[:150]}...")
        return {"success": True, "response": response_json}
    
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"❌ HTTP Error with Gemini: {http_err}")
        error_detail = response.text if 'response' in locals() else "No response"
        logger.error(f"Response content: {error_detail}")
        return {"success": False, "error": f"HTTP Error: {http_err}", "response": error_detail}
    
    except Exception as e:
        logger.error(f"❌ Error with Gemini: {e}")
        return {"success": False, "error": str(e)}

def test_clean_url_version(model_id, original_url):
    """
    Test a Gemini model with both the original URL and a clean version without query parameters.
    
    Args:
        model_id (str): The OpenRouter model ID for Gemini
        original_url (str): The original image URL to test
        
    Returns:
        dict: A dictionary with results for both URL versions
    """
    # Test with original URL
    logger.info(f"\nTesting ORIGINAL URL with {model_id}...")
    original_result = test_gemini_with_image(model_id, original_url)
    
    # If the original URL has query parameters, test with a clean version
    parsed_url = urllib.parse.urlparse(original_url)
    if parsed_url.query:
        # Create a clean version without query parameters
        clean_url = create_clean_url(original_url)
        
        # Test with clean URL
        logger.info(f"\nTesting CLEAN URL with {model_id}...")
        clean_result = test_gemini_with_image(model_id, clean_url)
        
        # Return both results
        return {
            "model": model_id,
            "original_url": {
                "url": original_url,
                "success": original_result["success"],
                "response": original_result
            },
            "clean_url": {
                "url": clean_url,
                "success": clean_result["success"],
                "response": clean_result
            }
        }
    else:
        # URL was already clean, return just the original result
        return {
            "model": model_id,
            "original_url": {
                "url": original_url,
                "success": original_result["success"],
                "response": original_result
            },
            "clean_url": None  # No clean URL version needed
        }

def main():
    """
    Run tests for Gemini models with different image URL formats.
    """
    # Check if we have any image URLs to test
    if not IMAGE_URLS:
        logger.error("No image URLs provided for testing")
        return
    
    results = []
    
    # Test each Gemini model with each image URL
    for model_id in GEMINI_MODELS:
        model_results = []
        
        for image_url in IMAGE_URLS:
            logger.info(f"\n{'=' * 80}\nTesting {model_id} with image URL\n{'=' * 80}")
            
            # Test both original and clean URL versions
            result = test_clean_url_version(model_id, image_url)
            model_results.append(result)
            
            # Add a delay between requests
            time.sleep(2)
        
        results.append({
            "model": model_id,
            "test_results": model_results
        })
    
    # Write results to file
    with open("gemini_url_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    logger.info("\n\n==== GEMINI TEST SUMMARY ====")
    for model_result in results:
        model_id = model_result["model"]
        logger.info(f"\nModel: {model_id}")
        
        success_count = 0
        total_tests = 0
        
        for test in model_result["test_results"]:
            # Original URL test
            original_success = test["original_url"]["success"]
            success_indicator = "✅" if original_success else "❌"
            logger.info(f"{success_indicator} Original URL: {test['original_url']['url'][:50]}...")
            
            total_tests += 1
            if original_success:
                success_count += 1
            
            # Clean URL test (if available)
            if test["clean_url"]:
                clean_success = test["clean_url"]["success"]
                success_indicator = "✅" if clean_success else "❌"
                logger.info(f"{success_indicator} Clean URL: {test['clean_url']['url'][:50]}...")
                
                total_tests += 1
                if clean_success:
                    success_count += 1
        
        # Calculate success rate
        success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
        logger.info(f"Success rate for {model_id}: {success_rate:.1f}% ({success_count}/{total_tests})")

if __name__ == "__main__":
    main()