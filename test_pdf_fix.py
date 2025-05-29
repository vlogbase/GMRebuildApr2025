#!/usr/bin/env python3
"""
Quick test to verify PDF upload returns base64 data URL format
"""
import requests
import io
import base64
from reportlab.pdfgen import canvas

def create_test_pdf():
    """Create a simple test PDF in memory"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 750, "Test PDF Document")
    p.drawString(100, 730, "This is a test PDF for upload verification")
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

def test_pdf_upload():
    """Test the PDF upload endpoint"""
    print("Creating test PDF...")
    pdf_data = create_test_pdf()
    
    # Create a file-like object for the request
    files = {
        'file': ('test.pdf', io.BytesIO(pdf_data), 'application/pdf')
    }
    
    print("Testing PDF upload...")
    try:
        response = requests.post('http://localhost:5000/upload_file', files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"Success: {result.get('success')}")
            print(f"File type: {result.get('file_type')}")
            print(f"Filename: {result.get('filename')}")
            
            # Check if document_url is in the correct base64 format
            document_url = result.get('document_url', '')
            if document_url.startswith('data:application/pdf;base64,'):
                print("✅ PDF is in correct base64 data URL format!")
                print(f"Base64 length: {len(document_url)} characters")
                return True
            else:
                print(f"❌ Wrong format. Expected 'data:application/pdf;base64,', got: {document_url[:50]}...")
                return False
        else:
            print(f"❌ Upload failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing upload: {e}")
        return False

if __name__ == "__main__":
    success = test_pdf_upload()
    if success:
        print("\n🎉 PDF upload fix is working correctly!")
    else:
        print("\n💥 PDF upload still has issues")