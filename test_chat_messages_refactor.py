"""
Test script to validate the refactoring of chat_memory_manager.py to use a dedicated chat_messages collection.
This script verifies:
1. Proper message storage in the new collection
2. Retrieval from the new collection
3. Backward compatibility with existing chat_sessions
"""

import os
import sys
import uuid
import logging
import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our memory manager
from chat_memory_manager import ChatMemoryManager

def test_chat_messages_refactoring():
    """Test the refactored chat_memory_manager.py with dedicated chat_messages collection"""
    
    try:
        # Create a memory manager instance
        logger.info("Initializing ChatMemoryManager...")
        memory_manager = ChatMemoryManager()
        
        # Generate unique test IDs
        test_session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Using test session ID: {test_session_id}")
        logger.info(f"Using test user ID: {test_user_id}")
        
        # Step 1: Add a new message
        logger.info("\n=== STEP 1: Add a new message ===")
        test_message = "This is a test message for the refactored chat_messages collection."
        
        result = memory_manager.add_message(
            session_id=test_session_id,
            user_id=test_user_id,
            role="user",
            content=test_message
        )
        
        if not result:
            logger.error("❌ Failed to add message")
            return False
            
        logger.info("✅ Successfully added message")
        
        # Step 2: Add another message
        logger.info("\n=== STEP 2: Add another message ===")
        test_message_2 = "This is a second test message with different content."
        
        result = memory_manager.add_message(
            session_id=test_session_id,
            user_id=test_user_id,
            role="assistant",
            content=test_message_2
        )
        
        if not result:
            logger.error("❌ Failed to add second message")
            return False
            
        logger.info("✅ Successfully added second message")
        
        # Step 3: Retrieve messages chronologically
        logger.info("\n=== STEP 3: Retrieve messages chronologically ===")
        recent_messages = memory_manager.retrieve_short_term_memory(
            session_id=test_session_id,
            user_id=test_user_id,
            query_text="",  # Empty to test chronological retrieval only
            last_n=10
        )
        
        if not recent_messages or len(recent_messages) != 2:
            logger.error(f"❌ Failed to retrieve expected number of messages. Got {len(recent_messages) if recent_messages else 0}, expected 2")
            return False
            
        logger.info(f"✅ Successfully retrieved {len(recent_messages)} messages chronologically")
        
        # Step 4: Verify the message contents
        logger.info("\n=== STEP 4: Verify message contents ===")
        first_content = recent_messages[0]["content"]
        second_content = recent_messages[1]["content"]
        
        logger.info(f"Message 1: {first_content[:50]}...")
        logger.info(f"Message 2: {second_content[:50]}...")
        
        if test_message not in (first_content, second_content) or test_message_2 not in (first_content, second_content):
            logger.error("❌ Retrieved messages don't match original content")
            return False
            
        logger.info("✅ Message contents verified correctly")
        
        # Step 5: Test semantic retrieval (requires proper index setup)
        logger.info("\n=== STEP 5: Test semantic retrieval (may fail without proper index) ===")
        try:
            semantic_messages = memory_manager.retrieve_short_term_memory(
                session_id=test_session_id,
                user_id=test_user_id,
                query_text="Tell me about test messages",
                last_n=5,
                vector_search_limit=2
            )
            
            logger.info(f"Semantic retrieval returned {len(semantic_messages)} messages")
            logger.info("Note: Full vector search functionality requires the 'chat_messages_vector_index' to be created in MongoDB Atlas")
            
        except Exception as e:
            logger.warning(f"⚠️ Semantic retrieval test generated an exception (this may be expected without proper index setup): {e}")
        
        # Step 6: Verify session metadata in chat_sessions collection
        logger.info("\n=== STEP 6: Verify session metadata ===")
        session_metadata = memory_manager.db.chat_sessions.find_one({"session_id": test_session_id})
        
        if not session_metadata:
            logger.error("❌ Failed to find session metadata in chat_sessions collection")
            return False
            
        if "last_message_preview" not in session_metadata:
            logger.error("❌ Session metadata is missing expected fields like 'last_message_preview'")
            return False
            
        logger.info(f"✅ Session metadata verified. Last message preview: {session_metadata.get('last_message_preview', '')[:50]}...")
        
        # Final status
        logger.info("\n=== REFACTORING TEST COMPLETE ===")
        logger.info("✅ All basic functionality tests passed!")
        logger.info("Note: Full vector search capabilities require manual creation of the 'chat_messages_vector_index' in MongoDB Atlas")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Check if MongoDB URI is set
    if not os.environ.get("MONGODB_ATLAS_URI"):
        logger.error("MONGODB_ATLAS_URI environment variable not set")
        sys.exit(1)
    
    # Run the test
    success = test_chat_messages_refactoring()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)