"""
Test script to examine multimodal image compatibility across different AI models.

This script tests different image formats and URLs with multiple OpenRouter models
to identify why some images work with certain models but not others.
"""

import os
import requests
import base64
import json
import time
import logging
from urllib.parse import urlparse
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

# Models to test
models_to_test = [
    "google/gemini-2.5-pro-preview-03-25",
    "openai/gpt-4o",
    "anthropic/claude-3.7-sonnet"
]

# Test image URLs - we'll test both direct URLs and Azure Blob Storage URLs
test_image_urls = [
    # Add your test image URLs here
    # If you have Azure Blob Storage URLs, include them as well
]

# Generic test function with detailed logging
def test_model_with_image(model_id, image_url, prompt_text="What's in this image?"):
    """
    Test a model with an image URL and log detailed information about the request and response.
    
    Args:
        model_id (str): The OpenRouter model ID to test
        image_url (str): The image URL to test
        prompt_text (str): The prompt text to send with the image
        
    Returns:
        dict: The response from the API
    """
    # Log detailed info about the image URL
    parsed_url = urlparse(image_url)
    domain = parsed_url.netloc
    path = parsed_url.path
    extension = os.path.splitext(path)[1].lower()
    has_query_params = bool(parsed_url.query)
    
    logger.info(f"Testing model: {model_id}")
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
    
    # Multimodal content format - should work across all OpenRouter models
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
        'stream': False  # Don't stream for testing purposes
    }
    
    try:
        logger.info(f"Sending request to OpenRouter...")
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=60  # Generous timeout for multimodal models
        )
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Log response
        response_json = response.json()
        content = response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
        model_used = response_json.get('model', 'unknown')
        
        logger.info(f"✅ Success with model: {model_used}")
        logger.info(f"Response (first 150 chars): {content[:150]}...")
        return response_json
    
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"❌ HTTP Error: {http_err}")
        logger.error(f"Response content: {response.text}")
        return {"error": f"HTTP Error: {http_err}", "response": response.text}
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"error": str(e)}

# Create helper to generate test image in different formats
def generate_test_images():
    """
    Generate test images in different formats (JPEG, PNG, WebP) and save them locally.
    Then upload them to Azure Blob Storage if credentials are available.
    
    Returns:
        list: URLs of uploaded images
    """
    # Create a simple test image
    img = Image.new('RGB', (300, 200), color=(255, 0, 0))
    
    # Save in different formats
    image_paths = []
    for fmt in ['JPEG', 'PNG', 'WEBP']:
        filename = f"test_image.{fmt.lower()}"
        img.save(filename, fmt)
        image_paths.append(filename)
        logger.info(f"Created test image: {filename}")
    
    # If Azure credentials are available, upload images
    azure_connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    azure_container_name = os.environ.get("AZURE_STORAGE_CONTAINER_NAME")
    
    if azure_connection_string and azure_container_name:
        from azure.storage.blob import BlobServiceClient, ContentSettings
        
        image_urls = []
        try:
            # Create the BlobServiceClient
            blob_service_client = BlobServiceClient.from_connection_string(azure_connection_string)
            
            # Get a client to interact with the container
            container_client = blob_service_client.get_container_client(azure_container_name)
            
            # Upload each image
            for image_path in image_paths:
                with open(image_path, 'rb') as data:
                    # Get content type based on file extension
                    content_type = f"image/{os.path.splitext(image_path)[1][1:].lower()}"
                    if content_type == "image/jpg":
                        content_type = "image/jpeg"
                    
                    # Upload blob with content type metadata
                    blob_name = f"test_multimodal/{image_path}"
                    content_settings = ContentSettings(content_type=content_type)
                    
                    blob_client = container_client.upload_blob(
                        name=blob_name,
                        data=data,
                        content_settings=content_settings,
                        overwrite=True
                    )
                    
                    # Generate a SAS URL for the uploaded blob
                    from datetime import datetime, timedelta
                    from azure.storage.blob import generate_blob_sas, BlobSasPermissions
                    
                    sas_token = generate_blob_sas(
                        account_name=blob_service_client.account_name,
                        container_name=azure_container_name,
                        blob_name=blob_name,
                        account_key=blob_service_client.credential.account_key,
                        permission=BlobSasPermissions(read=True),
                        expiry=datetime.utcnow() + timedelta(hours=1)
                    )
                    
                    sas_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{azure_container_name}/{blob_name}?{sas_token}"
                    image_urls.append(sas_url)
                    
                    # Also add a public URL without SAS token if container is public
                    public_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{azure_container_name}/{blob_name}"
                    image_urls.append(public_url)
                    
                    logger.info(f"Uploaded {image_path} to Azure Blob Storage")
                    logger.info(f"SAS URL: {sas_url[:100]}...")
                    logger.info(f"Public URL: {public_url}")
            
            return image_urls
        except Exception as e:
            logger.error(f"Error uploading to Azure Blob Storage: {e}")
            return []
    else:
        logger.warning("Azure Blob Storage credentials not found, skipping upload")
        return []

def main():
    """
    Run the compatibility tests for different models and image URLs.
    """
    # Generate test images if no URLs are provided
    if not test_image_urls:
        logger.info("No test image URLs provided, generating test images...")
        generated_urls = generate_test_images()
        if generated_urls:
            test_image_urls.extend(generated_urls)
        else:
            logger.error("Failed to generate test images and no URLs provided")
            return
    
    results = []
    
    # Test each model with each image URL
    for model_id in models_to_test:
        for image_url in test_image_urls:
            logger.info(f"\n{'=' * 80}\nTesting {model_id} with image {image_url[:50]}...\n{'=' * 80}")
            result = test_model_with_image(model_id, image_url)
            
            # Store result
            results.append({
                "model": model_id,
                "image_url": image_url,
                "success": "error" not in result,
                "response": result
            })
            
            # Add a small delay between requests to avoid rate limiting
            time.sleep(2)
    
    # Write results to file
    with open("multimodal_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    logger.info("\n\n==== TEST SUMMARY ====")
    for result in results:
        success_indicator = "✅" if result["success"] else "❌"
        logger.info(f"{success_indicator} {result['model']} with {result['image_url'][:50]}...")
    
if __name__ == "__main__":
    main()