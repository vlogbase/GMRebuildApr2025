"""
Test script for uploading an image directly using the Azure Blob Storage implementation
"""
import os
import io
import uuid
import logging
from pathlib import Path
from PIL import Image
from azure.storage.blob import BlobServiceClient, ContentSettings

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_test_image(width=300, height=200, color=(255, 0, 0)):
    """Generate a simple test image with the specified dimensions and color."""
    img = Image.new('RGB', (width, height), color=color)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

def test_upload_image():
    """Test uploading an image to Azure Blob Storage."""
    try:
        # Get Azure storage credentials from environment
        azure_connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        azure_container_name = os.environ.get("AZURE_STORAGE_CONTAINER_NAME")
        
        if not azure_connection_string or not azure_container_name:
            logger.error("Missing Azure Storage credentials")
            return False
        
        # Create BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(azure_connection_string)
        
        # Get container client
        container_client = blob_service_client.get_container_client(azure_container_name)
        
        # Check if container exists, if not create it
        try:
            container_properties = container_client.get_container_properties()
            logger.info(f"Container {azure_container_name} exists")
        except Exception as container_error:
            logger.info(f"Container {azure_container_name} does not exist, creating it...")
            container_client = blob_service_client.create_container(azure_container_name)
            logger.info(f"Container {azure_container_name} created successfully")
        
        # Generate a test image
        logger.info("Generating test image...")
        test_image = generate_test_image()
        test_image_data = test_image.read()
        
        # Generate a unique filename
        unique_filename = f"test_upload_{uuid.uuid4().hex}.jpg"
        logger.info(f"Generated unique filename: {unique_filename}")
        
        # Create a blob client for the specific blob
        blob_client = container_client.get_blob_client(unique_filename)
        
        # Set content settings (MIME type)
        content_settings = ContentSettings(content_type='image/jpeg')
        
        # Upload the image data to Azure Blob Storage
        logger.info("Uploading image to Azure Blob Storage...")
        blob_client.upload_blob(
            data=test_image_data,
            content_settings=content_settings,
            overwrite=True
        )
        
        # Generate a public URL for the uploaded image
        image_url = blob_client.url
        logger.info(f"Image uploaded successfully. URL: {image_url}")
        
        return True, image_url
    except Exception as e:
        logger.exception(f"Error uploading image: {e}")
        return False, None

if __name__ == "__main__":
    success, url = test_upload_image()
    if success:
        print("\n✅ Image upload to Azure Blob Storage successful!")
        print(f"Image URL: {url}")
    else:
        print("\n❌ Image upload to Azure Blob Storage failed!")