"""
Simple script to test Azure Blob Storage integration for image uploads.
This directly tests the upload functionality without going through the Flask app.
"""
import os
import io
import uuid
from pathlib import Path
from PIL import Image
from azure.storage.blob import BlobServiceClient, ContentSettings

def test_azure_upload():
    # Get Azure Storage credentials from environment
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.environ.get("AZURE_STORAGE_CONTAINER_NAME")
    
    if not connection_string or not container_name:
        print("❌ Missing Azure Storage credentials")
        return False
    
    try:
        # Create a test image
        img = Image.new('RGB', (100, 100), color = 'red')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        # Generate a unique filename
        unique_filename = f"{uuid.uuid4().hex}.jpg"
        
        # Create the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Get a client to interact with the container
        container_client = blob_service_client.get_container_client(container_name)
        
        # Create a blob client for the specific blob
        blob_client = container_client.get_blob_client(unique_filename)
        
        # Set content settings (MIME type)
        content_settings = ContentSettings(content_type='image/jpeg')
        
        # Upload the image data to Azure Blob Storage
        blob_client.upload_blob(
            data=img_io.getvalue(),
            content_settings=content_settings,
            overwrite=True
        )
        
        print(f"✅ Successfully uploaded test image to Azure Blob Storage: {unique_filename}")
        return True
    
    except Exception as e:
        print(f"❌ Error uploading to Azure Blob Storage: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Azure Blob Storage integration...")
    result = test_azure_upload()
    if result:
        print("🎉 Test passed! Azure Blob Storage is working correctly")
    else:
        print("❌ Test failed! Check the error messages above")