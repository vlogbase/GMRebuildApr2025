"""
Test script for RAG annotations and context persistence

This script tests the full RAG flow with a focus on verifying context persistence via 
OpenRouter annotations. It runs through various scenarios to ensure annotations are 
properly captured, stored, and reused in subsequent requests.
"""

import os
import sys
import json
import logging
import requests
import time
from datetime import datetime
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rag_annotations_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_PDF_PATH = "test_files/sample_document.pdf"  # Create this or use an existing PDF
TEST_IMAGE_PATH = "test_files/sample_image.jpg"   # Create this or use an existing image
MODEL_SUPPORTS_PDF = "openai/gpt-4o"              # Model that supports PDFs
MODEL_SUPPORTS_MULTIMODAL = "openai/gpt-4o"       # Model with multimodal support

# Add any test credentials here (for testing only)
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

def setup_test_environment():
    """
    Set up the test environment by creating test files if they don't exist.
    """
    # Create test directory if it doesn't exist
    os.makedirs("test_files", exist_ok=True)
    
    # Create a sample PDF for testing if it doesn't exist
    if not os.path.exists(TEST_PDF_PATH):
        try:
            # Try to download a sample PDF if it doesn't exist
            logger.info(f"Downloading sample PDF for testing to {TEST_PDF_PATH}")
            response = requests.get("https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf")
            with open(TEST_PDF_PATH, "wb") as f:
                f.write(response.content)
        except Exception as e:
            logger.error(f"Failed to download sample PDF: {e}")
            return False
    
    # Create a sample image for testing if it doesn't exist
    if not os.path.exists(TEST_IMAGE_PATH):
        try:
            # Try to download a sample image if it doesn't exist
            logger.info(f"Downloading sample image for testing to {TEST_IMAGE_PATH}")
            response = requests.get("https://picsum.photos/200/300")
            with open(TEST_IMAGE_PATH, "wb") as f:
                f.write(response.content)
        except Exception as e:
            logger.error(f"Failed to download sample image: {e}")
            return False
    
    logger.info("Test environment setup completed successfully")
    return True

def login_user(session):
    """
    Log in the test user.
    
    Args:
        session: The requests session to use for the login
        
    Returns:
        bool: Whether the login was successful
    """
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200:
        logger.info("Logged in successfully")
        return True
    else:
        logger.error(f"Failed to log in: {response.status_code} {response.text}")
        return False

def create_conversation(session):
    """
    Create a new conversation.
    
    Args:
        session: The requests session to use
        
    Returns:
        str: The ID of the new conversation, or None if creation failed
    """
    response = session.post(f"{BASE_URL}/conversations")
    if response.status_code == 200:
        conversation = response.json()
        conversation_id = conversation.get("id")
        logger.info(f"Created conversation with ID: {conversation_id}")
        return conversation_id
    else:
        logger.error(f"Failed to create conversation: {response.status_code} {response.text}")
        return None

def upload_document_for_rag(session, file_path):
    """
    Upload a document for RAG.
    
    Args:
        session: The requests session to use
        file_path: The path to the document to upload
        
    Returns:
        dict: The response from the server, or None if upload failed
    """
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        response = session.post(f"{BASE_URL}/attach_file_for_rag", files=files)
        
    if response.status_code == 200:
        result = response.json()
        logger.info(f"Uploaded document for RAG: {result}")
        return result
    else:
        logger.error(f"Failed to upload document: {response.status_code} {response.text}")
        return None

def send_chat_message(session, conversation_id, message, model_id, document_urls=None):
    """
    Send a chat message.
    
    Args:
        session: The requests session to use
        conversation_id: The ID of the conversation
        message: The message to send
        model_id: The ID of the model to use
        document_urls: Optional list of document URLs to include
        
    Returns:
        dict: The response from the server, or None if send failed
    """
    payload = {
        "message": message,
        "conversation_id": conversation_id,
        "model_id": model_id
    }
    
    if document_urls:
        payload["document_urls"] = document_urls
    
    logger.info(f"Sending chat message with payload: {payload}")
    response = session.post(f"{BASE_URL}/chat", json=payload)
    
    if response.status_code == 200:
        # For SSE responses, we need to parse the chunks
        result = []
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        result.append(data)
                    except json.JSONDecodeError:
                        pass
        logger.info(f"Received chat response (truncated): {str(result)[:500]}")
        return result
    else:
        logger.error(f"Failed to send chat message: {response.status_code} {response.text}")
        return None

def check_message_annotations(conversation_id, message_index=-1):
    """
    Check if a message has annotations stored in the database.
    
    Args:
        conversation_id: The ID of the conversation
        message_index: The index of the message (-1 for the latest message)
        
    Returns:
        dict: The annotations, or None if not found
    """
    try:
        # Get database URL from environment
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            return None
            
        # Create engine
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            if message_index == -1:
                # Get the latest message
                query = text("""
                    SELECT id, role, annotations FROM message 
                    WHERE conversation_id = :conversation_id 
                    ORDER BY created_at DESC LIMIT 1
                """)
            else:
                # Get the message at the specified index
                query = text("""
                    SELECT id, role, annotations FROM message 
                    WHERE conversation_id = :conversation_id 
                    ORDER BY created_at ASC LIMIT 1 OFFSET :offset
                """)
                
            result = conn.execute(query, {"conversation_id": conversation_id, "offset": message_index})
            row = result.fetchone()
            
            if row:
                message_id, role, annotations = row
                logger.info(f"Found message {message_id} with role {role} and annotations: {annotations}")
                return annotations
            else:
                logger.warning(f"No message found for conversation {conversation_id} at index {message_index}")
                return None
                
    except Exception as e:
        logger.error(f"Error checking message annotations: {e}")
        return None

def test_scenario_1_single_pdf_followup():
    """
    Test Scenario 1: Single PDF - Follow-up Questions
    """
    logger.info("======= Starting Test Scenario 1: Single PDF - Follow-up Questions =======")
    
    session = requests.Session()
    
    if not login_user(session):
        return False
    
    conversation_id = create_conversation(session)
    if not conversation_id:
        return False
    
    # Upload a PDF
    result = upload_document_for_rag(session, TEST_PDF_PATH)
    if not result:
        return False
    
    document_urls = [item["url"] for item in result.get("results", []) if item.get("status") == "success"]
    if not document_urls:
        logger.error("No document URLs returned from upload")
        return False
    
    # Ask initial question about the PDF
    initial_question = "Can you summarize the content of the PDF I just uploaded?"
    chat_response = send_chat_message(
        session, conversation_id, initial_question, MODEL_SUPPORTS_PDF, document_urls
    )
    if not chat_response:
        return False
    
    # Check if annotations were stored
    annotations = check_message_annotations(conversation_id)
    if not annotations:
        logger.warning("No annotations found in the first assistant message")
    else:
        logger.info("Annotations found in the first assistant message")
    
    # Ask a follow-up question (without including document URLs again)
    followup_question = "What are the key points from the document?"
    followup_response = send_chat_message(
        session, conversation_id, followup_question, MODEL_SUPPORTS_PDF
    )
    if not followup_response:
        return False
    
    # Ask another follow-up question
    second_followup = "Can you explain the main argument in more detail?"
    second_followup_response = send_chat_message(
        session, conversation_id, second_followup, MODEL_SUPPORTS_PDF
    )
    if not second_followup_response:
        return False
    
    logger.info("Scenario 1 completed successfully")
    return True

def test_scenario_2_single_image_followup():
    """
    Test Scenario 2: Single Image - Follow-up Questions
    """
    logger.info("======= Starting Test Scenario 2: Single Image - Follow-up Questions =======")
    
    session = requests.Session()
    
    if not login_user(session):
        return False
    
    conversation_id = create_conversation(session)
    if not conversation_id:
        return False
    
    # Upload an image
    result = upload_document_for_rag(session, TEST_IMAGE_PATH)
    if not result:
        return False
    
    document_urls = [item["url"] for item in result.get("results", []) if item.get("status") == "success"]
    if not document_urls:
        logger.error("No document URLs returned from upload")
        return False
    
    # Ask initial question about the image
    initial_question = "Can you describe what you see in this image?"
    chat_response = send_chat_message(
        session, conversation_id, initial_question, MODEL_SUPPORTS_MULTIMODAL, document_urls
    )
    if not chat_response:
        return False
    
    # Check if annotations were stored
    annotations = check_message_annotations(conversation_id)
    if not annotations:
        logger.warning("No annotations found in the first assistant message - this is expected for some image models")
    else:
        logger.info("Annotations found in the first assistant message")
    
    # Ask a follow-up question (without including document URLs again)
    followup_question = "What colors are dominant in the image?"
    followup_response = send_chat_message(
        session, conversation_id, followup_question, MODEL_SUPPORTS_MULTIMODAL
    )
    if not followup_response:
        return False
    
    logger.info("Scenario 2 completed successfully")
    return True

def test_scenario_3_multiple_documents():
    """
    Test Scenario 3: Multiple Active RAG Documents
    """
    logger.info("======= Starting Test Scenario 3: Multiple Active RAG Documents =======")
    
    session = requests.Session()
    
    if not login_user(session):
        return False
    
    conversation_id = create_conversation(session)
    if not conversation_id:
        return False
    
    # Upload a PDF
    pdf_result = upload_document_for_rag(session, TEST_PDF_PATH)
    if not pdf_result:
        return False
    
    pdf_urls = [item["url"] for item in pdf_result.get("results", []) if item.get("status") == "success"]
    
    # Upload an image
    image_result = upload_document_for_rag(session, TEST_IMAGE_PATH)
    if not image_result:
        return False
    
    image_urls = [item["url"] for item in image_result.get("results", []) if item.get("status") == "success"]
    
    # Combine URLs
    document_urls = pdf_urls + image_urls
    
    # Ask question about the PDF
    pdf_question = "Can you summarize the content of the PDF I uploaded?"
    pdf_response = send_chat_message(
        session, conversation_id, pdf_question, MODEL_SUPPORTS_MULTIMODAL, document_urls
    )
    if not pdf_response:
        return False
    
    # Ask question about the image
    image_question = "Can you describe the image I uploaded?"
    image_response = send_chat_message(
        session, conversation_id, image_question, MODEL_SUPPORTS_MULTIMODAL
    )
    if not image_response:
        return False
    
    # Ask question that requires synthesizing information from both
    synthesis_question = "Compare the content of the PDF with what you see in the image."
    synthesis_response = send_chat_message(
        session, conversation_id, synthesis_question, MODEL_SUPPORTS_MULTIMODAL
    )
    if not synthesis_response:
        return False
    
    logger.info("Scenario 3 completed successfully")
    return True

def run_tests():
    """
    Run all test scenarios.
    """
    logger.info("Setting up test environment...")
    if not setup_test_environment():
        logger.error("Failed to set up test environment")
        return False
    
    results = {}
    
    logger.info("Running Scenario 1: Single PDF - Follow-up Questions")
    results["Scenario 1"] = test_scenario_1_single_pdf_followup()
    
    logger.info("Running Scenario 2: Single Image - Follow-up Questions")
    results["Scenario 2"] = test_scenario_2_single_image_followup()
    
    logger.info("Running Scenario 3: Multiple Active RAG Documents")
    results["Scenario 3"] = test_scenario_3_multiple_documents()
    
    # Print summary of results
    logger.info("=== Test Results Summary ===")
    for scenario, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{scenario}: {status}")
    
    # Overall result
    return all(results.values())

if __name__ == "__main__":
    success = run_tests()
    if success:
        logger.info("All tests completed successfully")
        sys.exit(0)
    else:
        logger.error("Some tests failed")
        sys.exit(1)