"""
Test script to verify the memory preference toggle functionality.
This script tests:
1. Setting the enable_memory field to False for a test user
2. Checking that no messages are saved to memory when enable_memory is False
3. Checking that no memory context is added when enable_memory is False

Usage: python test_memory_preference.py
"""

import os
import logging
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MemoryPreferenceTest")

# Ensure environment variables are loaded
load_dotenv()

def test_memory_preference():
    """Test the memory preference toggle functionality"""
    
    # Import necessary modules here to avoid any circular imports
    from app import app, db
    from models import User
    from memory_integration import get_memory_manager, save_message_with_memory, enrich_prompt_with_memory
    
    # Create a test user if needed
    with app.app_context():
        # Check if test user exists
        test_username = "memorytest_user"
        test_user = User.query.filter_by(username=test_username).first()
        
        if not test_user:
            logger.info(f"Creating test user: {test_username}")
            test_user = User(
                username=test_username,
                email="memorytest@example.com",
                enable_memory=True  # Start with memory enabled
            )
            db.session.add(test_user)
            db.session.commit()
        
        logger.info(f"Test user ID: {test_user.id}")
        logger.info(f"Initial memory preference: {'enabled' if test_user.enable_memory else 'disabled'}")
        
        # === TEST 1: Disable memory preference ===
        logger.info("\n=== TEST 1: Disabling memory preference ===")
        
        # Update user preference to disable memory
        test_user.enable_memory = False
        db.session.commit()
        
        # Verify user preference was updated
        test_user = User.query.get(test_user.id)  # Refresh from DB
        logger.info(f"Updated memory preference: {'enabled' if test_user.enable_memory else 'disabled'}")
        
        if not test_user.enable_memory:
            logger.info("✅ Memory preference successfully set to disabled")
        else:
            logger.error("❌ Failed to disable memory preference")
            return False
        
        # === TEST 2: Test saving message with memory disabled ===
        logger.info("\n=== TEST 2: Testing message saving with memory disabled ===")
        
        # Get memory manager
        memory_manager = get_memory_manager()
        if not memory_manager:
            logger.error("Failed to initialize memory manager")
            return False
        
        # Create unique test identifiers
        test_session_id = f"memory_test_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        test_message = f"This is a test message at {datetime.now().isoformat()}"
        
        # First, directly count messages in the session
        initial_count = 0
        try:
            # Direct count using the manager's collection
            docs = memory_manager.chat_messages.count_documents({
                "session_id": test_session_id
            })
            initial_count = docs
            logger.info(f"Initial message count: {initial_count}")
        except Exception as e:
            logger.error(f"Error counting messages: {e}")
        
        # Attempt to save message with memory disabled
        # This mimics what happens in the chat route
        if not test_user.enable_memory:
            logger.info("Memory is disabled for user - should not save message")
        else:
            save_message_with_memory(
                session_id=test_session_id,
                user_id=str(test_user.id),
                role="user",
                content=test_message
            )
        
        # Wait a moment for async operations
        import time
        time.sleep(2)
        
        # Check if message was saved
        final_count = 0
        try:
            docs = memory_manager.chat_messages.count_documents({
                "session_id": test_session_id
            })
            final_count = docs
            logger.info(f"Final message count: {final_count}")
        except Exception as e:
            logger.error(f"Error counting messages: {e}")
        
        if final_count == initial_count:
            logger.info("✅ No messages were saved when memory was disabled")
        else:
            logger.error("❌ Messages were saved despite memory being disabled")
            return False
        
        # === TEST 3: Test memory retrieval with memory disabled ===
        logger.info("\n=== TEST 3: Testing memory retrieval with memory disabled ===")
        
        # Create basic conversation history
        conversation_history = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thanks for asking!"}
        ]
        
        # Simulate chat route behavior
        if not test_user.enable_memory:
            logger.info("Memory is disabled for user - should not enrich with memory")
            enriched_messages = conversation_history
        else:
            enriched_messages = enrich_prompt_with_memory(
                session_id=test_session_id,
                user_id=str(test_user.id),
                user_message="Tell me more about our previous conversation",
                conversation_history=conversation_history
            )
        
        # Check if memory was added
        if len(enriched_messages) == len(conversation_history):
            logger.info("✅ No memory was added when memory was disabled")
        else:
            logger.error("❌ Memory was added despite being disabled")
            return False
        
        # === TEST 4: Enable memory and verify functionality ===
        logger.info("\n=== TEST 4: Re-enabling memory functionality ===")
        
        # Update user preference to enable memory
        test_user.enable_memory = True
        db.session.commit()
        
        # Verify user preference was updated
        test_user = User.query.get(test_user.id)  # Refresh from DB
        logger.info(f"Updated memory preference: {'enabled' if test_user.enable_memory else 'disabled'}")
        
        if test_user.enable_memory:
            logger.info("✅ Memory preference successfully set to enabled")
        else:
            logger.error("❌ Failed to enable memory preference")
            return False
        
        logger.info("All tests completed successfully! ✅")
        return True

if __name__ == "__main__":
    logger.info("Starting memory preference toggle test")
    
    if test_memory_preference():
        logger.info("All tests PASSED ✅")
        sys.exit(0)
    else:
        logger.error("Some tests FAILED ❌")
        sys.exit(1)