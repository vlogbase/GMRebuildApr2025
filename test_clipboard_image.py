"""
Simple test script to verify the image upload and formatting functionality.
This script uses flask's test client to simulate uploading an image and 
checks if the response format is correct.
"""
import io
import json
import base64
from PIL import Image

# Import app from app.py
from app import app

def generate_test_image(width=300, height=200, color=(255, 0, 0)):
    """
    Generate a simple test image for upload testing
    
    Args:
        width: Width of the test image
        height: Height of the test image
        color: RGB color tuple for the test image
        
    Returns:
        BytesIO object containing the image data
    """
    # Create a simple red rectangle image
    image = Image.new("RGB", (width, height), color=color)
    img_io = io.BytesIO()
    image.save(img_io, format='JPEG')
    img_io.seek(0)
    return img_io

def test_image_upload():
    """Test the image upload endpoint"""
    # Create a test client
    client = app.test_client()
    
    # Generate a test image
    test_image = generate_test_image()
    
    # Upload the image using the /upload_image endpoint
    response = client.post(
        '/upload_image',
        data={'file': (test_image, 'test_image.jpg', 'image/jpeg')},
        content_type='multipart/form-data'
    )
    
    # Check if the response is OK
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    # Parse the response JSON
    data = json.loads(response.data)
    
    # Check if the response contains the expected fields
    assert 'success' in data, "Response missing 'success' field"
    assert data['success'] is True, f"Expected success=True, got {data['success']}"
    assert 'image_url' in data, "Response missing 'image_url' field"
    
    print("✅ Image upload test passed!")
    print(f"Image URL: {data['image_url']}")
    
    return data['image_url']

if __name__ == "__main__":
    print("Testing image upload functionality...")
    image_url = test_image_upload()
    print("\nTesting complete!")