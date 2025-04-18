"""
Simple test script to verify the multi-image functionality for the chat application.
This simulates how the backend processes multiple images in a message.
"""

import json
import os
from urllib.parse import urlparse

# Simulate a request with multiple images
def test_multi_image_message():
    print("Testing multi-image message processing...\n")
    
    # Sample data that would be coming from the frontend
    data = {
        "message": "Here are multiple test images:",
        "model": "google/gemini-pro-vision",
        "image_urls": [
            "https://example.com/image1.jpg",
            "https://example.com/image2.png",
            "https://example.com/image3.webp",
            "https://example.blob.core.windows.net/container/image4.jpg?sp=r&st=2023..."
        ]
    }
    
    # Print the incoming data
    print("Received data from frontend:")
    print(json.dumps(data, indent=2))
    print()

    # Extract data
    user_message = data.get("message", "")
    image_urls = data.get("image_urls", [])
    model = data.get("model", "default_model")
    
    print(f"Processing message with {len(image_urls)} images for model: {model}")
    
    # Create multimodal content array
    multimodal_content = [
        {"type": "text", "text": user_message}
    ]
    
    # Process each image URL
    for i, url in enumerate(image_urls):
        print(f"\nProcessing image {i+1}: {url}")
        
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            print(f"❌ Invalid URL format: {url}")
            continue
            
        # Analyze URL
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            path = parsed_url.path
            extension = os.path.splitext(path)[1].lower()
            has_query = bool(parsed_url.query)
            
            print(f"  Domain: {domain}")
            print(f"  Path: {path}")
            print(f"  Extension: {extension}")
            print(f"  Has query params: {has_query}")
            
            # Check for special processing needs
            if "gemini" in model.lower() and has_query:
                print("  ⚠️ Warning: Gemini model with query parameters may have issues")
                
            if extension == ".webp" and "gemini" in model.lower():
                print("  ⚠️ Warning: WebP format with Gemini model may have issues")
                
        except Exception as e:
            print(f"  Error analyzing URL: {str(e)}")
            
        # Add to multimodal content
        multimodal_content.append({
            "type": "image_url", 
            "image_url": {"url": url}
        })
    
    # Create final payload
    payload = {
        "role": "user",
        "content": multimodal_content
    }
    
    print("\nFinal message payload:")
    print(json.dumps(payload, indent=2))
    
    # Simulated model response
    print("\nModel would receive message with text and multiple images")
    print(f"Total content items: {len(multimodal_content)}")
    print(f"Text content: {multimodal_content[0]['text'] if len(multimodal_content) > 0 else 'None'}")
    print(f"Image count: {len(multimodal_content) - 1}")
    
if __name__ == "__main__":
    test_multi_image_message()