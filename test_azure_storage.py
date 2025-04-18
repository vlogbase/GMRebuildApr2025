"""
Test Azure Blob Storage functionality for image uploads
"""
import os
import io
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image
import logging

from azure.storage.blob import BlobServiceClient, ContentSettings, generate_blob_sas, BlobSasPermissions

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

def test_azure_blob_storage():
    """Test uploading an image to Azure Blob Storage and generating URLs."""
    try:
        # Get connection string and container name from environment variables
        azure_connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        azure_container_name = os.environ.get("AZURE_STORAGE_CONTAINER_NAME")
        
        if not azure_connection_string or not azure_container_name:
            logger.error("Missing Azure Storage credentials")
            return False
            
        # Create the BlobServiceClient
        logger.info("Creating BlobServiceClient...")
        blob_service_client = BlobServiceClient.from_connection_string(azure_connection_string)
        
        # Get a client to interact with the container
        logger.info(f"Getting container client for {azure_container_name}...")
        container_client = blob_service_client.get_container_client(azure_container_name)
        
        # Check if container exists, if not create it
        logger.info(f"Checking if container {azure_container_name} exists...")
        try:
            container_properties = container_client.get_container_properties()
            logger.info(f"Container {azure_container_name} exists")
        except Exception as e:
            logger.info(f"Container {azure_container_name} does not exist, creating it...")
            container_client = blob_service_client.create_container(azure_container_name)
            logger.info(f"Container {azure_container_name} created successfully")
        
        # Generate a test image
        logger.info("Generating test image...")
        test_image = generate_test_image()
        test_image_data = test_image.read()
        
        # Generate a unique filename
        unique_filename = f"test_{uuid.uuid4().hex}.jpg"
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
        
        # Generate a public URL
        logger.info("Generating public URL...")
        public_url = blob_client.url
        logger.info(f"Public URL: {public_url}")
        
        # Generate a SAS token URL
        logger.info("Generating SAS token URL...")
        
        # Get account information from connection string
        account_name = None
        account_key = None
        
        # Parse connection string to extract account name and key
        # Connection string format: DefaultEndpointsProtocol=https;AccountName=xxx;AccountKey=xxx;EndpointSuffix=core.windows.net
        conn_str_parts = azure_connection_string.split(';')
        for part in conn_str_parts:
            if '=' in part:
                key, value = part.split('=', 1)
                if key.lower() == 'accountname':
                    account_name = value
                elif key.lower() == 'accountkey':
                    account_key = value
        
        if not account_name or not account_key:
            logger.error("Unable to extract account information from connection string")
            return False
            
        # Generate SAS token
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=azure_container_name,
            blob_name=unique_filename,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(seconds=3600)
        )
        
        # Full URL with SAS token
        sas_url = f"{blob_client.url}?{sas_token}"
        logger.info(f"SAS URL: {sas_url}")
        
        return True
    except Exception as e:
        logger.exception(f"Error testing Azure Blob Storage: {e}")
        return False

if __name__ == "__main__":
    success = test_azure_blob_storage()
    if success:
        print("\n✅ Azure Blob Storage test successful!")
    else:
        print("\n❌ Azure Blob Storage test failed!")