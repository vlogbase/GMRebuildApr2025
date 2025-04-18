"""
Test script to inspect the available methods on the Replit Object Storage Client.
"""
import os
import sys
import inspect
from replit.object_storage import Client

print("\n=== Inspecting Replit Object Storage Client API ===\n")

# Get the bucket ID
bucket_id = os.environ.get("REPLIT_OBJECT_STORAGE_BUCKET_ID")

if not bucket_id:
    print("❌ ERROR: REPLIT_OBJECT_STORAGE_BUCKET_ID environment variable is missing")
    sys.exit(1)

# Create client
client = Client(bucket_id=bucket_id)

# Get all methods
methods = inspect.getmembers(client, predicate=inspect.ismethod)

print("Available methods on Client object:")
for name, method in methods:
    # Skip private methods
    if name.startswith('_'):
        continue
        
    # Get signature
    try:
        signature = str(inspect.signature(method))
    except ValueError:
        signature = "(unknown)"
        
    print(f"- {name}{signature}")

print("\n=== Client Inspection Complete ===\n")
