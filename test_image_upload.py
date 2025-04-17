"""
Tests for the image upload functionality with Replit Object Storage.
This test file tests the image upload functionality directly using Flask test client.
"""
import os
import json
from pathlib import Path
from PIL import Image
import io
import base64
import unittest

# Import Flask app directly
from app import app

def generate_test_image(width=300, height=200):
    """
    Generate a test image for uploading.
    
    Args:
        width (int): Width of the image in pixels
        height (int): Height of the image in pixels
        
    Returns:
        io.BytesIO: The image data as a binary stream
    """
    # Create a simple test image - red rectangle
    image = Image.new("RGB", (width, height), color=(255, 0, 0))
    img_io = io.BytesIO()
    image.save(img_io, format='JPEG')
    img_io.seek(0)
    return img_io

def test_image_upload_endpoint():
    """Test the image upload endpoint with a test image."""
    # Create a test client
    client = app.test_client()
    
    # Generate a test image
    test_image = generate_test_image()
    
    # Make the request using Flask's test client
    response = client.post(
        '/upload_image',
        data={'file': (test_image, 'test_image.jpg', 'image/jpeg')},
        content_type='multipart/form-data'
    )
    
    # Check response status
    assert response.status_code == 200, f"Expected 200 OK but got {response.status_code}: {response.data}"
    
    # Parse response
    data = json.loads(response.data)
    
    # Validate response format
    assert 'success' in data, "Missing 'success' key in response"
    assert data['success'] is True, "Upload was not successful"
    assert 'image_url' in data, "Missing 'image_url' key in response"
    
    # Validate URL format
    image_url = data['image_url']
    assert isinstance(image_url, str), "image_url should be a string"
    assert len(image_url) > 0, "image_url should not be empty"
    
    # Note: We can't easily check if the URL is accessible in a test environment
    # without making an actual HTTP request, which we'll skip for unit testing
    
    print(f"Successfully uploaded image at: {image_url}")
    return image_url

def test_invalid_file_type():
    """Test that non-image files are rejected."""
    # Create a test client
    client = app.test_client()
    
    # Create a text file
    text_io = io.BytesIO(b"This is not an image")
    
    # Make the request using Flask's test client
    response = client.post(
        '/upload_image',
        data={'file': (text_io, 'test.txt', 'text/plain')},
        content_type='multipart/form-data'
    )
    
    # Should get a 400 Bad Request
    assert response.status_code == 400, f"Expected 400 Bad Request but got {response.status_code}"
    
    # Parse response
    data = json.loads(response.data)
    
    # Validate error message
    assert 'error' in data, "Missing 'error' key in response"
    assert 'supported' in data['error'].lower(), "Error message should mention supported formats"

def test_no_file_provided():
    """Test the error handling when no file is provided."""
    # Create a test client
    client = app.test_client()
    
    # Make the request with no file
    response = client.post('/upload_image')
    
    # Should get a 400 Bad Request
    assert response.status_code == 400, f"Expected 400 Bad Request but got {response.status_code}"
    
    # Parse response
    data = json.loads(response.data)
    
    # Validate error message
    assert 'error' in data, "Missing 'error' key in response"
    assert 'no file' in data['error'].lower(), "Error message should mention no file provided"

class TestImageUpload(unittest.TestCase):
    """Test class for the image upload functionality"""
    
    def test_all(self):
        """Run all tests"""
        test_image_upload_endpoint()
        test_invalid_file_type()
        test_no_file_provided()

if __name__ == "__main__":
    # Run the tests directly if the script is executed
    print("Testing image upload functionality...")
    try:
        with app.app_context():
            image_url = test_image_upload_endpoint()
            print("✅ Image upload test passed!")
            
            test_invalid_file_type()
            print("✅ Invalid file type test passed!")
            
            test_no_file_provided()
            print("✅ No file provided test passed!")
            
            print(f"All tests passed successfully! Uploaded image URL: {image_url}")
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")