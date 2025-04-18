"""
Test script to verify our updated image upload functionality.
"""
import io
import json
import logging
from PIL import Image
from app import app

# Suppress verbose logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('document_processor').setLevel(logging.ERROR)
logging.getLogger('ChatMemoryManager').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)

def generate_test_image(width=300, height=200):
    """Generate a test image with a red rectangle."""
    image = Image.new("RGB", (width, height), color=(255, 0, 0))
    img_io = io.BytesIO()
    image.save(img_io, format='JPEG')
    img_io.seek(0)
    return img_io

print("\n=== Testing Image Upload with Fixed API Methods ===\n")

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
        
        # Test the API with the image URL
        print("\nTesting the chat API with the uploaded image...")
        chat_response = client.post(
            '/chat',
            json={
                'message': 'Describe this image',
                'image_url': data['image_url'],
                'model': 'anthropic/claude-3-opus-20240229'  # A multimodal model
            },
            content_type='application/json'
        )
        
        print(f"Chat API status code: {chat_response.status_code}")
        if chat_response.status_code == 200:
            chat_data = json.loads(chat_response.data)
            print("Chat API response (truncated):")
            print(chat_data.get('text', '')[:100] + "..." if chat_data.get('text') else "No text in response")
        else:
            print(f"Chat API error: {chat_response.data.decode('utf-8')}")
else:
    print(f"❌ ERROR: Upload failed with status code {response.status_code}")
    print(f"Response: {response.data.decode('utf-8')}")

print("\n=== Test Complete ===\n")
