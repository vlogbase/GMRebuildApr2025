"""
Test script to verify PDF uploads are working properly
"""

import logging
import os
import requests
import base64
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pdf_upload_test.log')
    ]
)

logger = logging.getLogger(__name__)

# Load PDF test file - create a simple one if it doesn't exist
TEST_PDF_PATH = "test_document.pdf"

def create_test_pdf():
    """Create a simple test PDF file if it doesn't exist"""
    if os.path.exists(TEST_PDF_PATH):
        logger.info(f"Using existing test PDF: {TEST_PDF_PATH}")
        return True
        
    try:
        from reportlab.pdfgen import canvas
        
        logger.info(f"Creating test PDF: {TEST_PDF_PATH}")
        c = canvas.Canvas(TEST_PDF_PATH)
        c.drawString(100, 750, "Test PDF Document")
        c.drawString(100, 700, f"Created on {datetime.now().isoformat()}")
        c.drawString(100, 650, "This is a test document for PDF upload functionality")
        c.save()
        
        logger.info(f"Successfully created test PDF: {TEST_PDF_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error creating test PDF: {e}")
        
        # Create a minimal PDF if reportlab is not available
        with open(TEST_PDF_PATH, "wb") as f:
            f.write(b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Resources<<>>>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF")
        
        logger.info(f"Created minimal test PDF: {TEST_PDF_PATH}")
        return os.path.exists(TEST_PDF_PATH)

def test_pdf_upload(server_url="http://localhost:5000"):
    """Test PDF upload endpoint"""
    upload_endpoint = f"{server_url}/upload_file"
    
    # Create or use existing test PDF
    if not create_test_pdf():
        logger.error("Failed to create test PDF")
        return False
    
    # Read the test PDF
    try:
        with open(TEST_PDF_PATH, "rb") as f:
            pdf_data = f.read()
        
        logger.info(f"Read test PDF, size: {len(pdf_data)} bytes")
        
        # Prepare multipart form data
        files = {"file": (TEST_PDF_PATH, pdf_data, "application/pdf")}
        data = {"conversation_id": "test"}
        
        # Make the request
        logger.info(f"Sending PDF upload request to {upload_endpoint}")
        response = requests.post(upload_endpoint, files=files, data=data)
        
        # Check response
        if response.status_code == 200:
            logger.info(f"Upload successful: {response.json()}")
            return True
        else:
            logger.error(f"Upload failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error testing PDF upload: {e}")
        return False

def test_pdf_chat(server_url="http://localhost:5000"):
    """Test sending a chat message with PDF attachment"""
    chat_endpoint = f"{server_url}/chat"
    
    # Create test PDF and encode it as base64
    if not create_test_pdf():
        logger.error("Failed to create test PDF")
        return False
    
    try:
        # Read and encode PDF
        with open(TEST_PDF_PATH, "rb") as f:
            pdf_data = f.read()
        
        pdf_base64 = base64.b64encode(pdf_data).decode("utf-8")
        pdf_data_url = f"data:application/pdf;base64,{pdf_base64}"
        
        # Prepare chat message with PDF
        payload = {
            "conversation_id": "test",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Here's a PDF document for analysis"},
                        {"type": "file", "file": {"filename": TEST_PDF_PATH, "file_data": pdf_data_url}}
                    ]
                }
            ],
            "model": "google/gemini-1.5-pro-latest"  # Use a model that supports PDFs
        }
        
        # Send request
        logger.info(f"Sending chat request with PDF to {chat_endpoint}")
        response = requests.post(chat_endpoint, json=payload)
        
        # Check response
        if response.status_code == 200:
            logger.info(f"Chat with PDF successful: {response.text[:100]}...")
            return True
        else:
            logger.error(f"Chat with PDF failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error testing chat with PDF: {e}")
        return False

def run_tests():
    """Run all PDF support tests"""
    logger.info("=== Starting PDF Support Tests ===")
    
    # Get server URL from environment or use default
    server_url = os.environ.get("SERVER_URL", "http://localhost:5000")
    
    # Run tests
    upload_result = test_pdf_upload(server_url)
    chat_result = test_pdf_chat(server_url)
    
    # Print summary
    logger.info("=== PDF Support Test Results ===")
    logger.info(f"PDF Upload Test: {'✅ PASSED' if upload_result else '❌ FAILED'}")
    logger.info(f"PDF Chat Test: {'✅ PASSED' if chat_result else '❌ FAILED'}")
    
    # Overall result
    if upload_result and chat_result:
        logger.info("🎉 All PDF support tests passed!")
        return True
    else:
        logger.error("⚠️ Some PDF support tests failed.")
        return False

if __name__ == "__main__":
    run_tests()