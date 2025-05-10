"""
Workflow to test the document conversation fixes.
This workflow tests if documents are properly scoped to their conversations.
"""

import os
import sys
import logging
from flask import session
from app import app, db, document_processor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("document_conversation_test")

def run():
    """
    Run the test workflow for document conversation scoping.
    """
    try:
        with app.app_context():
            logger.info("Starting document conversation test workflow")
            
            # Test with mock user and conversations
            user_id = "test_user_123"
            conversation_id_1 = "test_conversation_1"
            conversation_id_2 = "test_conversation_2"
            
            # Initialize document processor
            from document_processor import DocumentProcessor
            doc_processor = DocumentProcessor()
            
            # Create a test document for conversation 1
            test_doc_text = """
            Conversation-Specific Document Context
            
            This document demonstrates how the RAG system isolates document context 
            between different conversations. Each document is scoped to the conversation
            where it was uploaded, ensuring that:
            
            1. Documents from one conversation don't appear in other conversations
            2. Each conversation has its own isolated document context
            3. Users can upload different documents to different conversations
            
            This document is specific to conversation 1.
            """
            
            # Create a test document for conversation 2
            test_doc_text_2 = """
            Second Conversation Document
            
            This document is only for conversation 2, and should never appear
            in the context for conversation 1. This demonstrates proper 
            conversation isolation in the RAG system.
            
            When a user uploads documents in different conversations, they should
            remain isolated to those specific conversations.
            """
            
            # Process and store the test documents with their respective conversation IDs
            logger.info("Creating test document for conversation 1")
            import io
            doc1_stream = io.BytesIO(test_doc_text.encode('utf-8'))
            doc_processor.process_and_store_document(doc1_stream, "test_doc_conv1.txt", user_id, conversation_id_1)
            
            logger.info("Creating test document for conversation 2")
            doc2_stream = io.BytesIO(test_doc_text_2.encode('utf-8'))
            doc_processor.process_and_store_document(doc2_stream, "test_doc_conv2.txt", user_id, conversation_id_2)
            
            # For demonstration: 
            # Generate a sample query
            query = "How does the RAG system work?"
            
            # 2. Retrieve chunks with conversation_id_1
            logger.info(f"Testing retrieval with conversation_id_1: {conversation_id_1}")
            chunks_1 = doc_processor.retrieve_relevant_chunks(
                query_text=query,
                user_id=user_id,
                conversation_id=conversation_id_1
            )
            logger.info(f"Found {len(chunks_1)} chunks for conversation 1")

            # 3. Retrieve chunks with conversation_id_2
            logger.info(f"Testing retrieval with conversation_id_2: {conversation_id_2}")
            chunks_2 = doc_processor.retrieve_relevant_chunks(
                query_text=query,
                user_id=user_id,
                conversation_id=conversation_id_2
            )
            logger.info(f"Found {len(chunks_2)} chunks for conversation 2")
            
            # 4. Retrieve chunks with no conversation_id (should return all user's docs)
            logger.info(f"Testing retrieval with no conversation_id filter")
            chunks_all = doc_processor.retrieve_relevant_chunks(
                query_text=query,
                user_id=user_id
            )
            logger.info(f"Found {len(chunks_all)} chunks with no conversation filter")
            
            logger.info("Document conversation test workflow completed")
            
    except Exception as e:
        logger.error(f"Error in document conversation test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()