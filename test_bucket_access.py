"""
Test script to check if we can access the Replit Object Storage bucket with just the bucket ID.
This test checks if the Replit environment automatically provides access.
"""
import os
import sys
import logging
from replit.object_storage import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("object_storage_test")

# Get the bucket ID
bucket_id = os.environ.get("REPLIT_OBJECT_STORAGE_BUCKET_ID")

print("\n=== Testing Replit Object Storage Access with just Bucket ID ===\n")

if not bucket_id:
    print("❌ ERROR: REPLIT_OBJECT_STORAGE_BUCKET_ID environment variable is missing")
    sys.exit(1)

print(f"✓ Found REPLIT_OBJECT_STORAGE_BUCKET_ID: {bucket_id}")
    
try:
    # Try to initialize the client with just the bucket ID
    # This works in the Replit environment if the repl has access to this bucket
    client = Client(bucket_id=bucket_id)
    
    # Try to list objects
    print("Attempting to list objects in the bucket...")
    objects = list(client.list())
    
    print(f"✓ Successfully connected to Replit Object Storage")
    print(f"✓ Found {len(objects)} objects in the storage bucket")
    
    # Try uploading a test file
    print("\nAttempting to upload a test file...")
    test_content = b"This is a test file to verify write access"
    test_object_name = "test-access-verification.txt"
    
    client.upload_from(
        test_object_name, 
        test_content,
        content_type="text/plain"
    )
    
    print(f"✓ Successfully uploaded test file: {test_object_name}")
    
    # Verify the file exists
    objects = list(client.list())
    test_object_exists = any(obj.name == test_object_name for obj in objects)
    
    if test_object_exists:
        print("✓ Test file verified in bucket listing")
    else:
        print("⚠️ Test file upload appeared successful but not found in listing")
    
    # Clean up test file
    try:
        client.delete(test_object_name)
        print("✓ Test file successfully deleted after verification")
    except Exception as e:
        print(f"⚠️ Could not delete test file: {e}")
        
except Exception as e:
    print(f"❌ ERROR connecting to Replit Object Storage: {e}")
    print("\nThe Replit environment might not have automatic access to this bucket.")
    print("You will need to provide the REPLIT_OBJECT_STORAGE_KEY_ID and REPLIT_OBJECT_STORAGE_SECRET.")

print("\n=== Test complete ===\n")
