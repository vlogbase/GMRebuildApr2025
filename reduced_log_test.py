"""
A simplified verification script for testing image uploads with reduced logging.
"""
import io
import json
import logging
import os
from PIL import Image
from app import app

# Suppress most logging
for logger_name in ['document_processor', 'ChatMemoryManager', 'urllib3', 'root']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

def generate_test_image(width=300, height=200):
    """Generate a test image with a red rectangle."""
    image = Image.new("RGB", (width, height), color=(255, 0, 0))
    img_io = io.BytesIO()
    image.save(img_io, format='JPEG')
    img_io.seek(0)
    return img_io

if __name__ == "__main__":
    print("\n=======================================")
    print("TESTING IMAGE UPLOAD FUNCTIONALITY")
    print("=======================================\n")
    
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
    else:
        print(f"❌ ERROR: Upload failed with status code {response.status_code}")
        print(f"Response: {response.data.decode('utf-8')}")
    
    print("\n=======================================")
    print("TEST COMPLETE")
    print("=======================================\n")
