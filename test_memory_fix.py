#!/usr/bin/env python3
"""
Test script to verify the fixes for the long-term memory component of the chatbot system.
This script tests:
1. Field name consistency between user_id and userId
2. Memory storage and retrieval functionality
3. Proper embedding generation

Usage: python test_memory_fix.py
"""

import os
import logging
import json
import sys
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MemoryTest")

# Ensure environment variables are loaded
load_dotenv()

def test_memory_system():
    """
    Test the memory system components with the new fixes
    """
    logger.info("Testing Memory System Components")
    
    # Import memory components
    try:
        from chat_memory_manager import ChatMemoryManager
        logger.info("Successfully imported ChatMemoryManager")
    except ImportError as e:
        logger.error(f"Failed to import ChatMemoryManager: {e}")
        return False
    
    # Initialize memory manager
    try:
        memory_manager = ChatMemoryManager()
        logger.info("Successfully initialized ChatMemoryManager")
    except Exception as e:
        logger.error(f"Failed to initialize ChatMemoryManager: {e}")
        return False
    
    # Test embedding generation
    try:
        test_text = "This is a test message for embedding generation."
        embedding = memory_manager._get_embedding(test_text)
        if embedding and len(embedding) == 3072:
            logger.info(f"Successfully generated embedding with {len(embedding)} dimensions")
        else:
            logger.error(f"Embedding generation failed or wrong dimensions: {len(embedding) if embedding else 'None'}")
            return False
    except Exception as e:
        logger.error(f"Error during embedding generation: {e}")
        return False
    
    # Test message storage
    test_user_id = "test_user_123"
    test_session_id = "test_session_456"
    test_message = "This is a test message to check field name consistency."
    
    try:
        result = memory_manager.add_message(
            session_id=test_session_id,
            user_id=test_user_id,
            role="user",
            content=test_message
        )
        
        if result:
            logger.info("Successfully added message to memory")
        else:
            logger.error("Failed to add message to memory")
            return False
    except Exception as e:
        logger.error(f"Error adding message to memory: {e}")
        return False
    
    # Test field name consistency
    try:
        # Check if the document has both user_id and userId fields
        session = memory_manager.chat_sessions.find_one({
            "session_id": test_session_id
        })
        
        if not session:
            logger.error(f"Could not find test session {test_session_id}")
            return False
            
        has_user_id = "user_id" in session
        has_userId = "userId" in session
        
        if has_user_id and has_userId:
            logger.info("Document has both user_id and userId fields ✓")
            logger.info(f"user_id: {session.get('user_id')}, userId: {session.get('userId')}")
            
            if session.get('user_id') == session.get('userId') == test_user_id:
                logger.info("Field values match correctly ✓")
            else:
                logger.error(f"Field values don't match: user_id={session.get('user_id')}, userId={session.get('userId')}")
                return False
        else:
            missing = []
            if not has_user_id:
                missing.append("user_id")
            if not has_userId:
                missing.append("userId")
            logger.error(f"Document is missing fields: {', '.join(missing)}")
            return False
    except Exception as e:
        logger.error(f"Error checking field name consistency: {e}")
        return False
    
    # Test memory retrieval
    try:
        memory_result = memory_manager.retrieve_long_term_memory(
            user_id=test_user_id,
            query_text="test message",
        )
        
        logger.info(f"Memory retrieval result: {json.dumps(memory_result, default=str)[:200]}...")
        logger.info("Successfully retrieved from long-term memory")
    except Exception as e:
        logger.error(f"Error retrieving from long-term memory: {e}")
        return False
    
    # Test memory enrichment (integration)
    try:
        from memory_integration import enrich_prompt_with_memory
        
        # Create a simple conversation history
        history = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you for asking!"}
        ]
        
        enriched = enrich_prompt_with_memory(
            session_id=test_session_id,
            user_id=test_user_id,
            user_message="Tell me more about yourself",
            conversation_history=history
        )
        
        logger.info(f"Original history length: {len(history)}, Enriched length: {len(enriched)}")
        
        if len(enriched) >= len(history):
            logger.info("Successfully tested memory integration")
        else:
            logger.error("Memory integration failed - enriched history is shorter than original")
            return False
    except Exception as e:
        logger.error(f"Error testing memory integration: {e}")
        return False
    
    logger.info("All memory system tests passed successfully! ✓")
    return True

if __name__ == "__main__":
    success = test_memory_system()
    if not success:
        logger.error("Memory system tests failed")
        sys.exit(1)
    else:
        logger.info("Memory system tests completed successfully")
        sys.exit(0)