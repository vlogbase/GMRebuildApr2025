"""
Minimal test script to isolate Azure Blob Storage initialization issue.
This script attempts to initialize the Azure BlobServiceClient without Gevent monkey patching.
"""
import os
import logging
from azure.storage.blob import BlobServiceClient, ContentSettings

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_azure_init():
    """
    Test Azure Blob Storage initialization without Gevent monkey patching.
    """
    try:
        # Get connection string and container name from environment variables
        azure_connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        azure_container_name = os.environ.get("AZURE_STORAGE_CONTAINER_NAME")
        
        if not azure_connection_string or not azure_container_name:
            logger.error("Missing Azure Storage credentials")
            return False
            
        logger.info("Initializing BlobServiceClient...")
        # Create the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(azure_connection_string)
        
        logger.info("Getting container client...")
        # Get a client to interact with the container
        container_client = blob_service_client.get_container_client(azure_container_name)
        
        # Check if container exists
        logger.info(f"Checking if container {azure_container_name} exists...")
        try:
            container_properties = container_client.get_container_properties()
            logger.info(f"Container {azure_container_name} exists")
        except Exception as container_error:
            logger.info(f"Container {azure_container_name} does not exist, creating it...")
            container_client = blob_service_client.create_container(azure_container_name)
            logger.info(f"Container {azure_container_name} created successfully")
        
        # Validate by trying to list blobs
        logger.info("Listing blobs to validate connection...")
        blobs = list(container_client.list_blobs(maxresults=1))
        logger.info(f"Found {len(blobs)} blobs")
        
        logger.info("Azure Blob Storage initialization successful")
        return True
    except Exception as e:
        logger.exception(f"Failed to initialize Azure Blob Storage: {e}")
        return False

if __name__ == "__main__":
    logger.info("Testing Azure Blob Storage initialization without Gevent...")
    success = test_azure_init()
    if success:
        print("\n✅ Azure Blob Storage initialized successfully without Gevent")
    else:
        print("\n❌ Azure Blob Storage initialization failed without Gevent")