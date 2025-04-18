"""
Minimal test of the upload endpoint focusing just on the upload feature,
with reduced logging noise.
"""
import io
import json
import logging
from PIL import Image
from app import app

# Set logging levels to reduce noise
logging.basicConfig(level=logging.ERROR)
for logger_name in ['document_processor', 'ChatMemoryManager', 'urllib3', 'root', 'app']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

def generate_test_image():
    """Generate a simple red test image."""
    image = Image.new("RGB", (300, 200), color=(255, 0, 0))
    img_io = io.BytesIO()
    image.save(img_io, format='JPEG')
    img_io.seek(0)
    return img_io

print("\n=== TESTING IMAGE UPLOAD FUNCTIONALITY ===\n")

# Create a test client
client = app.test_client()

# Generate and upload a test image
test_image = generate_test_image()
response = client.post(
    '/upload_image',
    data={'file': (test_image, 'test_image.jpg', 'image/jpeg')},
    content_type='multipart/form-data'
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.data.decode('utf-8')}")

if response.status_code == 200:
    data = json.loads(response.data)
    if data.get('success') and data.get('image_url'):
        print(f"\n✅ SUCCESS: Image uploaded successfully")
        print(f"Image URL: {data['image_url']}")
    else:
        print("\n❌ ERROR: Upload response format incorrect")
else:
    print(f"\n❌ ERROR: Upload failed with status code {response.status_code}")

print("\n=== TEST COMPLETE ===\n")
