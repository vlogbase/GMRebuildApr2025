"""
Test script to verify the PDF conversation fix
This script tests the fix for the conversation_uuid constraint issue when uploading PDFs
"""

import os
import base64
from flask import Flask, send_file, jsonify
from io import BytesIO
import logging
import sys
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def create_test_pdf():
    """
    Create a simple test PDF in memory
    Returns a BytesIO object containing a PDF file
    """
    try:
        # Use a simple text file as a placeholder if we can't create a PDF
        buffer = BytesIO()
        buffer.write(b"This is a test PDF file content")
        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.error(f"Error creating test PDF: {e}")
        return None

def test_upload_pdf():
    """
    Test uploading a PDF without a conversation_id
    This tests if our fix properly creates a conversation
    """
    logger.info("Testing PDF upload without conversation_id...")
    
    # Create a test PDF
    pdf_buffer = create_test_pdf()
    if not pdf_buffer:
        logger.error("Failed to create test PDF")
        return False
    
    # Prepare files for upload
    files = {'file': ('test.pdf', pdf_buffer, 'application/pdf')}
    
    # Upload to the server without providing a conversation_id
    upload_url = 'http://localhost:5000/upload_file'
    
    try:
        logger.info(f"Uploading PDF to {upload_url}...")
        response = requests.post(
            upload_url,
            files=files
        )
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Upload successful")
            
            # Verify that we got a conversation_id back
            if 'conversation_id' in data:
                logger.info(f"Success: Received conversation_id {data['conversation_id']}")
                return True
            else:
                logger.error("Failed: No conversation_id returned")
                return False
        else:
            logger.error(f"Failed with status {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error during test: {e}")
        return False

if __name__ == "__main__":
    success = test_upload_pdf()
    if success:
        print("✅ Test passed - conversation creation from PDF upload works!")
    else:
        print("❌ Test failed - PDF upload conversation creation issue still exists")
        exit(1)