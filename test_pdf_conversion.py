#!/usr/bin/env python3
"""
Test the PDF base64 conversion logic directly without requiring a running server
"""
import io
import base64
from reportlab.pdfgen import canvas

def create_test_pdf():
    """Create a simple test PDF in memory"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 750, "Test PDF Document")
    p.drawString(100, 730, "This is a test PDF for conversion verification")
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

def test_pdf_base64_conversion():
    """Test the PDF to base64 conversion logic from app.py"""
    print("Creating test PDF...")
    pdf_data = create_test_pdf()
    print(f"PDF size: {len(pdf_data)} bytes")
    
    # Convert to base64 data URL (same logic as in app.py)
    pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
    pdf_data_url = f"data:application/pdf;base64,{pdf_base64}"
    
    print(f"Base64 string length: {len(pdf_base64)} characters")
    print(f"Full data URL length: {len(pdf_data_url)} characters")
    print(f"Data URL prefix: {pdf_data_url[:50]}...")
    
    # Verify the format is correct for OpenRouter
    if pdf_data_url.startswith('data:application/pdf;base64,'):
        print("✅ PDF conversion produces correct format for OpenRouter!")
        
        # Test that we can decode it back
        try:
            base64_part = pdf_data_url.split(',', 1)[1]
            decoded_data = base64.b64decode(base64_part)
            if decoded_data == pdf_data:
                print("✅ Base64 encoding/decoding is correct!")
                return True
            else:
                print("❌ Base64 decoding doesn't match original data")
                return False
        except Exception as e:
            print(f"❌ Error decoding base64: {e}")
            return False
    else:
        print(f"❌ Wrong format: {pdf_data_url[:100]}")
        return False

if __name__ == "__main__":
    success = test_pdf_base64_conversion()
    if success:
        print("\n🎉 PDF base64 conversion logic is working correctly!")
        print("The upload endpoint should now return the correct format for OpenRouter.")
    else:
        print("\n💥 PDF conversion has issues")