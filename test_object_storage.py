"""
Test script to check Replit Object Storage functionality.
"""
import os
import logging
from replit.object_storage import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("object_storage_test")

# Get environment variables
bucket_id = os.environ.get("REPLIT_OBJECT_STORAGE_BUCKET_ID")
key_id = os.environ.get("REPLIT_OBJECT_STORAGE_KEY_ID")
key_secret = os.environ.get("REPLIT_OBJECT_STORAGE_SECRET")

print("\n=== Testing Replit Object Storage Access ===\n")

if not all([bucket_id, key_id, key_secret]):
    print("❌ ERROR: Missing required environment variables for Replit Object Storage")
    for var, name in [(bucket_id, "REPLIT_OBJECT_STORAGE_BUCKET_ID"), 
                      (key_id, "REPLIT_OBJECT_STORAGE_KEY_ID"), 
                      (key_secret, "REPLIT_OBJECT_STORAGE_SECRET")]:
        print(f"  - {name}: {'✓ Present' if var else '❌ Missing'}")
    print("\nPlease make sure these environment variables are set.")
else:
    print("✓ All required environment variables for Replit Object Storage are present")
    
    try:
        # Initialize the client
        client = Client(bucket_id=bucket_id)
        
        # Try to list objects
        objects = list(client.list())
        
        print(f"✓ Successfully connected to Replit Object Storage")
        print(f"✓ Found {len(objects)} objects in the storage bucket")
        
        # Print a few objects if any exist
        if objects:
            print("\nSample objects in storage:")
            for i, obj in enumerate(objects[:5]):
                print(f"  {i+1}. {obj.name}")
            if len(objects) > 5:
                print(f"  ... and {len(objects) - 5} more")
        
    except Exception as e:
        print(f"❌ ERROR connecting to Replit Object Storage: {e}")

print("\n=== Test complete ===\n")
