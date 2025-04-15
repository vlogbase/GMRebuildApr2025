"""
Test script for the ChatMemoryManager class.
This script requires environment variables to be set:
- MONGODB_ATLAS_URI: MongoDB Atlas connection string
- Either AZURE_OPENAI_* variables or OPENROUTER_API_KEY
"""

import os
import logging
import json
from dotenv import load_dotenv
from chat_memory_manager import ChatMemoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MemoryTest")

def test_memory_manager():
    """Run basic tests for ChatMemoryManager functionality"""
    # Check for required environment variables
    load_dotenv()
    required_vars = ['MONGODB_ATLAS_URI']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("Please set these environment variables and try again.")
        
        # Check if we have Azure OpenAI or OpenRouter
        if not os.environ.get('AZURE_OPENAI_API_KEY') and not os.environ.get('OPENROUTER_API_KEY'):
            logger.error("Missing either AZURE_OPENAI_API_KEY or OPENROUTER_API_KEY")
            logger.info("One of these must be set for embedding generation and LLM operations.")
        
        return False
    
    try:
        # Initialize the memory manager
        logger.info("Initializing ChatMemoryManager...")
        memory_manager = ChatMemoryManager()
        
        # Test session ID and user ID for testing
        session_id = "test_session_001"
        user_id = "test_user_001"
        
        # Test adding a message
        logger.info("Testing add_message...")
        test_message = "I love hiking in California and enjoy learning about AI technology."
        result = memory_manager.add_message(session_id, user_id, "user", test_message)
        if result:
            logger.info("✓ Successfully added message")
        else:
            logger.error("× Failed to add message")
            return False
        
        # Test retrieving short-term memory
        logger.info("Testing retrieve_short_term_memory...")
        query = "What outdoor activities do I enjoy?"
        messages = memory_manager.retrieve_short_term_memory(session_id, user_id, query)
        logger.info(f"Retrieved {len(messages)} messages from short-term memory")
        
        # Test extracting structured info
        logger.info("Testing extract_structured_info...")
        extracted = memory_manager.extract_structured_info(test_message)
        logger.info(f"Extracted info: {json.dumps(extracted, indent=2)}")
        
        # Test updating user profile
        if extracted:
            logger.info("Testing update_user_profile...")
            profile_updated = memory_manager.update_user_profile(user_id, extracted)
            if profile_updated:
                logger.info("✓ Successfully updated user profile")
            else:
                logger.error("× Failed to update user profile")
                return False
        
        # Test retrieving long-term memory
        logger.info("Testing retrieve_long_term_memory...")
        query = "What are my outdoor interests?"
        long_term = memory_manager.retrieve_long_term_memory(user_id, query)
        logger.info(f"Long-term memory facts: {json.dumps(long_term.get('matching_facts', {}), indent=2)}")
        logger.info(f"Similar preferences: {len(long_term.get('similar_preferences', []))}")
        
        # Test query rewriting
        logger.info("Testing rewrite_query...")
        chat_history = [
            {"role": "user", "content": "I'm planning a trip to Hawaii next month."},
            {"role": "assistant", "content": "That sounds wonderful! Hawaii is beautiful in any season. What kind of activities are you interested in doing there?"},
            {"role": "user", "content": "I'd like to try surfing and visit some volcanoes."}
        ]
        follow_up = "When is the best time to visit them?"
        rewritten = memory_manager.rewrite_query(chat_history, follow_up)
        logger.info(f"Original query: '{follow_up}'")
        logger.info(f"Rewritten query: '{rewritten}'")
        
        logger.info("All tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        return False

if __name__ == "__main__":
    test_memory_manager()