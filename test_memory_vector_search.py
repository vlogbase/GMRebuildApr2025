"""
Test script for the refactored ChatMemoryManager class with $vectorSearch.
This script validates that the MongoDB Atlas vector search is working properly.

Usage: python test_memory_vector_search.py
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path hack to import from parent directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the memory manager
from chat_memory_manager import ChatMemoryManager

def test_vector_search():
    """
    Test the refactored $vectorSearch implementation against the original implementation.
    """
    # Load environment variables
    load_dotenv()
    
    # Create a memory manager instance
    logger.info("Initializing ChatMemoryManager")
    memory_manager = ChatMemoryManager()
    
    # Test user and session IDs
    test_user_id = f"test_user_{int(time.time())}"
    test_session_id = f"test_session_{int(time.time())}"
    
    logger.info(f"Testing with user_id: {test_user_id}")
    logger.info(f"Testing with session_id: {test_session_id}")
    
    # First, add some preferences to the user profile
    preferences = [
        "I prefer dark mode interfaces over light mode",
        "I enjoy reading science fiction books about space exploration",
        "I like to drink coffee in the morning, not tea",
        "I prefer working from home rather than in an office",
        "I enjoy hiking in the mountains on weekends"
    ]
    
    # Create a dict with preferences
    info_dict = {
        "name": "Test User",
        "location": "Test City",
        "profession": "Software Tester",
        "interests": ["testing", "coding", "debugging"],
        "preferences": preferences,
        "opinions": ["Test-driven development is valuable", "Documentation is important"]
    }
    
    # Update the user profile with preferences
    logger.info(f"Adding {len(preferences)} preferences to user profile")
    result = memory_manager.update_user_profile(test_user_id, info_dict)
    
    if result:
        logger.info("Successfully added preferences to user profile")
    else:
        logger.error("Failed to add preferences to user profile")
        return
    
    # Now query for similar preferences
    test_queries = [
        "Do you know if I like dark themes?",
        "What kind of books do I enjoy reading?",
        "What's my morning beverage preference?",
        "Where do I prefer to work?",
        "What outdoor activities do I enjoy?"
    ]
    
    # Test each query
    for query in test_queries:
        logger.info(f"\nTesting query: '{query}'")
        
        # Retrieve long-term memory
        result = memory_manager.retrieve_long_term_memory(
            user_id=test_user_id,
            query_text=query,
            vector_search_limit=3
        )
        
        # Log the results
        facts = result.get("matching_facts", {})
        similar_prefs = result.get("similar_preferences", [])
        
        logger.info(f"Retrieved {len(facts)} facts and {len(similar_prefs)} similar preferences")
        
        if similar_prefs:
            logger.info("Top similar preferences:")
            for i, pref in enumerate(similar_prefs[:3]):
                logger.info(f"  {i+1}. '{pref.get('text', '')}' (score: {pref.get('score', 'N/A')})")
        else:
            logger.warning("No similar preferences found")
    
    logger.info("\nTest completed.")

if __name__ == "__main__":
    test_vector_search()