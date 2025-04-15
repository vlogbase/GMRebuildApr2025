"""
Integration module for connecting the ChatMemoryManager with the Flask chat application.
This module provides functions to enhance the chatbot with long-term memory capabilities.
"""

import logging
import asyncio
import time
from typing import List, Dict, Any, Optional
from functools import wraps

from chat_memory_manager import ChatMemoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MemoryIntegration")

# Create a global instance of ChatMemoryManager
# Note: This will be initialized when first accessed
_memory_manager = None

def get_memory_manager():
    """
    Get or initialize the global ChatMemoryManager instance.
    Uses lazy initialization to avoid startup errors if environment variables aren't configured.
    
    Returns:
        ChatMemoryManager or None: The memory manager instance, or None if initialization fails
    """
    global _memory_manager
    
    if _memory_manager is None:
        try:
            _memory_manager = ChatMemoryManager()
            logger.info("ChatMemoryManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChatMemoryManager: {e}")
    
    return _memory_manager

def async_task(f):
    """Decorator to run a function asynchronously in the background"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_in_executor(None, lambda: f(*args, **kwargs))
    return wrapper

@async_task
def save_message_with_memory(session_id: str, user_id: str, role: str, content: str):
    """
    Save a message to the memory system.
    This runs asynchronously to avoid blocking the response stream.
    
    Args:
        session_id (str): The conversation session ID
        user_id (str): The user ID
        role (str): Either "user" or "assistant"
        content (str): The message content
    """
    memory_manager = get_memory_manager()
    if not memory_manager:
        logger.warning("Message not saved to memory system - manager not initialized")
        return
    
    # Save the message
    result = memory_manager.add_message(session_id, user_id, role, content)
    
    # For user messages, extract information and update the user profile
    if role == "user" and result:
        try:
            extracted_info = memory_manager.extract_structured_info(content)
            if extracted_info:
                memory_manager.update_user_profile(user_id, extracted_info)
                logger.info(f"Updated user profile with extracted information for user {user_id}")
        except Exception as e:
            logger.error(f"Error extracting and saving user information: {e}")

def enrich_prompt_with_memory(
    session_id: str, 
    user_id: str, 
    user_message: str, 
    conversation_history: Optional[List[Dict]] = None
) -> List[Dict]:
    """
    Enhance the message history with relevant information from memory.
    
    Args:
        session_id (str): The conversation session ID
        user_id (str): The user ID
        user_message (str): The current user message
        conversation_history (List[Dict], optional): Recent conversation history
        
    Returns:
        List[Dict]: Enhanced message history with memory context
    """
    memory_manager = get_memory_manager()
    if not memory_manager:
        logger.warning("Cannot enrich prompt - memory manager not initialized")
        return conversation_history or []
    
    # Start with the provided history or empty list
    enhanced_history = conversation_history.copy() if conversation_history else []
    
    try:
        # Rewrite the query if it might be a follow-up question
        if conversation_history and len(conversation_history) > 1:
            rewritten_query = memory_manager.rewrite_query(conversation_history, user_message)
            # Only use rewritten query if it's significantly different
            if rewritten_query and len(rewritten_query) > len(user_message) * 1.2:
                search_query = rewritten_query
                logger.info(f"Rewrote query: '{user_message}' -> '{rewritten_query}'")
            else:
                search_query = user_message
        else:
            search_query = user_message
        
        # Retrieve relevant memory
        short_term = memory_manager.retrieve_short_term_memory(session_id, user_id, search_query)
        long_term = memory_manager.retrieve_long_term_memory(user_id, search_query)
        
        # Format long-term memory as context message if we have relevant information
        if long_term.get('matching_facts') or long_term.get('similar_preferences'):
            facts = long_term.get('matching_facts', {})
            preferences = [p.get('text') for p in long_term.get('similar_preferences', [])]
            
            if facts or preferences:
                context_parts = []
                
                if facts:
                    facts_str = ", ".join([f"{k}: {v}" for k, v in facts.items() 
                                         if k not in ('created_at', 'updated_at')])
                    if facts_str:
                        context_parts.append(f"User facts: {facts_str}")
                
                if preferences:
                    prefs_str = ", ".join(preferences[:3])  # Limit to top 3 preferences
                    if prefs_str:
                        context_parts.append(f"User preferences: {prefs_str}")
                
                if context_parts:
                    context_message = {
                        "role": "system",
                        "content": "Relevant user information:\n" + "\n".join(context_parts)
                    }
                    enhanced_history.insert(0, context_message)
                    logger.info("Added long-term memory context")
        
        # Potentially add relevant past messages that aren't in the recent history
        if short_term:
            # Convert history to set of content strings for easy comparison
            existing_content = {msg.get('content', '') for msg in enhanced_history}
            
            # Find relevant messages not already in history
            relevant_msgs = []
            for msg in short_term:
                content = msg.get('content', '')
                if content and content not in existing_content:
                    relevant_msgs.append({
                        "role": msg.get('role'),
                        "content": content
                    })
            
            # If we found relevant messages, add them with a marker
            if relevant_msgs:
                enhanced_history.insert(0, {
                    "role": "system",
                    "content": "The following are relevant messages from your previous conversation:"
                })
                enhanced_history[1:1] = relevant_msgs
                logger.info(f"Added {len(relevant_msgs)} relevant messages from memory")
        
        return enhanced_history
        
    except Exception as e:
        logger.error(f"Error enriching prompt with memory: {e}")
        return conversation_history or []