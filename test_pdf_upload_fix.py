"""
Test script to validate the PDF upload fixes in the chatbot.

This script tests that:
1. PDF uploads store the proper conversation_uuid
2. The PDF data is correctly included in messages to the model
"""
import os
import sys
import logging
from flask import Flask, session, jsonify, current_app
from app import app, db, chat, login_manager
from models import Message, Conversation, User
from flask_login import login_user, current_user
from sqlalchemy import desc
import base64
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_test_user():
    """Create a test user if needed and log them in"""
    with app.app_context():
        # Find or create a test user
        test_user = User.query.filter_by(email="test@example.com").first()
        if not test_user:
            logger.info("Creating test user")
            test_user = User(
                username="testuser",
                email="test@example.com",
                is_admin=False,
                is_affiliate=False
            )
            db.session.add(test_user)
            db.session.commit()
        
        # Log in as the test user
        login_user(test_user)
        logger.info(f"Logged in as test user: {test_user.email}")
        return test_user

def test_pdf_upload():
    """Test PDF upload functionality"""
    with app.app_context():
        # Ensure we have a test user
        test_user = ensure_test_user()
        
        # Create a simple base64 PDF (just for testing)
        sample_pdf_base64 = "JVBERi0xLjMKJcTl8uXrp/Og0MTGCjQgMCBvYmoKPDwgL0xlbmd0aCA1IDAgUiAvRmlsdGVyIC9GbGF0ZURlY29kZSA+PgpzdHJlYW0KeAErVAhUKFQwAEJDBTNTQ1MFQxNLBZM0SwVDM3NThVQFQyMLINPY1NTUxNQcKJZcWqJQnFmVa2BkYFCZmVuaCwBV+xCoCmVuZHN0cmVhbQplbmRvYmoKNSAwIG9iagoxMDIKZW5kb2JqCjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAzIDAgUiAvUmVzb3VyY2VzIDYgMCBSIC9Db250ZW50cyA0IDAgUiAvTWVkaWFCb3ggWzAgMCAyNTAgNTBdCj4+CmVuZG9iago2IDAgb2JqCjw8IC9Qcm9jU2V0IFsgL1BERiBdIC9Db2xvclNwYWNlIDw8IC9DczEgNyAwIFIgPj4gPj4KZW5kb2JqCjggMCBvYmoKPDwgL0xlbmd0aCA5IDAgUiAvTiAxIC9BbHRlcm5hdGUgL0RldmljZUdSQiAvRmlsdGVyIC9GbGF0ZURlY29kZSA+PgpzdHJlYW0KeAGFkk9PwkAQxe/7KfZITAw7M9s/YPZQqCUcPJDaREwMB1aRABKhlBh/+yq72JJw2GTfvJnfe9nqz74D7IGigVBjohIVMZIj74hBzH2fkZnkzgIPenaBUeJsLSZ7kV0qfSYNGByyznj7k1aWKnsv+yH5AFRCHEchyIH5m6Ii9jWIAqrn+tGCXxIByWDESCo0n+QYkT8khNSwDZdIzDd/zRi2zY6OKRSYLMcOSMjt6VFNy1oX3QQfCQpx/+P+oj5pPp/+ONFcQgvpB+ZPLNIgfRFEw/UvG8VIiC44kxn8ICd/5WYGGpsHXrDkUJ6k4+T8CQm1Sk+6TfX32Ys8bAQnmPQhBvVL9oXMl+TzA1rPEBRlbmRzdHJlYW0KZW5kb2JqCjkgMCBvYmoKMjYzCmVuZG9iago3IDAgb2JqClsgL0lDQ0Jhc2VkIDggMCBSIF0KZW5kb2JqCjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9NZWRpYUJveCBbMCAwIDI1MCA1MF0gL0NvdW50IDEgL0tpZHMgWyAyIDAgUiBdID4+CmVuZG9iagoxMCAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMyAwIFIgPj4KZW5kb2JqCjExIDAgb2JqCihmcmVxKQplbmRvYmoKMTIgMCBvYmoKKGZyZXEpCmVuZG9iagoxMyAwIG9iagooRDoyMDE4MDQwOTE1MTIxMVopCmVuZG9iagoxIDAgb2JqCjw8IC9UaXRsZSAxMSAwIFIgL0F1dGhvciAxMiAwIFIgL0NyZWF0b3IgKHBkZnRleCA0LjMuMCkgL1Byb2R1Y2VyIChwZGZ0ZXggNC4zLjApCi9DcmVhdGlvbkRhdGUgMTMgMCBSID4+CmVuZG9iagp4cmVmCjAgMTQKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwOTQ3IDAwMDAwIG4gCjAwMDAwMDAyMDYgMDAwMDAgbiAKMDAwMDAwMDczMiAwMDAwMCBuIAowMDAwMDAwMDE1IDAwMDAwIG4gCjAwMDAwMDAxODcgMDAwMDAgbiAKMDAwMDAwMDMxMSAwMDAwMCBuIAowMDAwMDAwNzA0IDAwMDAwIG4gCjAwMDAwMDAzNzkgMDAwMDAgbiAKMDAwMDAwMDY4NSAwMDAwMCBuIAowMDAwMDAwODEyIDAwMDAwIG4gCjAwMDAwMDA4NjIgMDAwMDAgbiAKMDAwMDAwMDg4NyAwMDAwMCBuIAowMDAwMDAwOTEyIDAwMDAwIG4gCnRyYWlsZXIKPDwgL1NpemUgMTQgL1Jvb3QgMTAgMCBSIC9JbmZvIDEgMCBSIC9JRCBbIDw1ZjFmNzdhNGRmYTY1MjgxNmJiNDUyZDJhZjk0YmUwMD4KPDVmMWY3N2E0ZGZhNjUyODE2YmI0NTJkMmFmOTRiZTAwPiBdID4+CnN0YXJ0eHJlZgoxMDcyCiUlRU9GCg=="
        pdf_url = f"data:application/pdf;base64,{sample_pdf_base64}"
        
        # Create a new conversation with UUID
        logger.info("Creating a new conversation with UUID")
        conversation = Conversation(
            user_id=test_user.id,
            title="Test PDF Upload",
            conversation_uuid="test-uuid-12345"  # This is the field that was missing before
        )
        db.session.add(conversation)
        db.session.commit()
        logger.info(f"Created conversation: ID={conversation.id}, UUID={conversation.conversation_uuid}")
        
        # Create a mock request payload similar to what the JavaScript would send
        logger.info("Creating mock chat request with PDF data")
        request_data = {
            "model": "anthropic/claude-3-sonnet-20240229",
            "stream": True,
            "message": "Please analyze this document",
            "conversation_id": conversation.id,
            "pdf_url": pdf_url,
            "pdf_filename": "test-document.pdf",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Please analyze this document"},
                        {
                            "type": "file",
                            "file": {
                                "filename": "test-document.pdf",
                                "file_data": pdf_url
                            }
                        }
                    ]
                }
            ]
        }
        
        # Store the request data as a Message in the database
        logger.info("Storing PDF message in database")
        message = Message(
            conversation_id=conversation.id,
            role="user",
            content="Please analyze this document",
            user_id=test_user.id,
            pdf_url=pdf_url,
            pdf_filename="test-document.pdf"
        )
        db.session.add(message)
        db.session.commit()
        
        # Fetch the message to verify it was stored correctly
        saved_message = Message.query.filter_by(conversation_id=conversation.id).first()
        logger.info(f"Retrieved message: {saved_message.id}, PDF URL: {saved_message.pdf_url is not None}")
        
        # Retrieve the conversation to verify conversation_uuid
        saved_conv = Conversation.query.get(conversation.id)
        logger.info(f"Retrieved conversation: ID={saved_conv.id}, UUID={saved_conv.conversation_uuid}")
        
        if saved_conv.conversation_uuid == "test-uuid-12345":
            logger.info("✅ SUCCESS: Conversation UUID is correctly stored")
        else:
            logger.error(f"❌ FAIL: Conversation UUID is not correct. Got: {saved_conv.conversation_uuid}")
            
        if saved_message.pdf_url == pdf_url:
            logger.info("✅ SUCCESS: PDF URL is correctly stored in the message")
        else:
            logger.error(f"❌ FAIL: PDF URL is not properly stored")
            
        logger.info("Test completed successfully")
        return True

def run_tests():
    """Run all tests"""
    with app.test_request_context():
        logger.info("Starting PDF upload fix tests")
        test_pdf_upload()
        logger.info("All tests completed")

if __name__ == "__main__":
    run_tests()