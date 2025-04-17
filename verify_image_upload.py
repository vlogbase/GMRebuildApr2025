"""
Simple verification script for the image upload functionality.
This script creates a test image and uploads it using the Flask test client.
"""
import os
import sys
import json
import io
import logging
from PIL import Image
from app import app

# Suppress verbose logging
logging.getLogger().setLevel(logging.ERROR)
for logger_name in ['document_processor', 'ChatMemoryManager', 'urllib3']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

def generate_test_image(width=300, height=200):
    """Generate a test image with a red rectangle."""
    image = Image.new("RGB", (width, height), color=(255, 0, 0))
    img_io = io.BytesIO()
    image.save(img_io, format='JPEG')
    img_io.seek(0)
    return img_io

if __name__ == "__main__":
    # Print a separator to make our output more visible
    print("\n" + "="*80)
    print("VERIFYING IMAGE UPLOAD FUNCTIONALITY")
    print("="*80 + "\n")
    
    # Create a test client
    client = app.test_client()
    
    # Generate a test image
    test_image = generate_test_image()
    
    # Make the request
    response = client.post(
        '/upload_image',
        data={'file': (test_image, 'test_image.jpg', 'image/jpeg')},
        content_type='multipart/form-data'
    )
    
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = json.loads(response.data)
        print(f"Response: {data}")
        
        if data.get('success') and data.get('image_url'):
            print(f"\n✅ SUCCESS: Image uploaded successfully")
            print(f"Image URL: {data['image_url']}")
            print(f"\nTo verify, this URL should point to the uploaded image")
            print(f"You can visit the test page at: /test-upload")
            
            # Try a second test - invalid file type
            print("\nTesting invalid file type rejection...")
            text_io = io.BytesIO(b"This is not an image")
            invalid_response = client.post(
                '/upload_image',
                data={'file': (text_io, 'test.txt', 'text/plain')},
                content_type='multipart/form-data'
            )
            
            if invalid_response.status_code == 400:
                invalid_data = json.loads(invalid_response.data)
                print(f"✅ SUCCESS: Invalid file properly rejected with error: {invalid_data.get('error', 'No error message')}")
            else:
                print(f"❌ ERROR: Invalid file should be rejected with 400 status, got {invalid_response.status_code}")
        else:
            print("❌ ERROR: Upload succeeded but response format is invalid")
    else:
        print(f"❌ ERROR: Upload failed with status code {response.status_code}")
        print(f"Response: {response.data.decode('utf-8')}")
        
    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80 + "\n")