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
    logger.info(f"MEMORY_INTEGRATION: Saving {role} message to memory for session {session_id}, user {user_id}")
    
    memory_manager = get_memory_manager()
    if not memory_manager:
        logger.warning("MEMORY_INTEGRATION: Message not saved - memory manager not initialized")
        return
    
    # Save the message
    logger.info(f"MEMORY_INTEGRATION: Sending message to ChatMemoryManager.add_message")
    result = memory_manager.add_message(session_id, user_id, role, content)
    
    if result:
        logger.info(f"MEMORY_INTEGRATION: Successfully saved message to memory system")
    else:
        logger.error(f"MEMORY_INTEGRATION: Failed to save message to memory system")
    
    # For user messages, extract information and update the user profile
    if role == "user" and result:
        try:
            logger.info(f"MEMORY_INTEGRATION: Extracting structured information from user message")
            extracted_info = memory_manager.extract_structured_info(content)
            
            if extracted_info:
                logger.info(f"MEMORY_INTEGRATION: Extracted information: {list(extracted_info.keys())}")
                
                # Check for non-empty fields
                non_empty_fields = []
                for key, value in extracted_info.items():
                    if value and (not isinstance(value, list) or len(value) > 0):
                        non_empty_fields.append(key)
                
                if non_empty_fields:
                    logger.info(f"MEMORY_INTEGRATION: Updating user profile with fields: {non_empty_fields}")
                    memory_manager.update_user_profile(user_id, extracted_info)
                    logger.info(f"MEMORY_INTEGRATION: Successfully updated user profile")
                else:
                    logger.info(f"MEMORY_INTEGRATION: No meaningful information extracted, skipping profile update")
            else:
                logger.info(f"MEMORY_INTEGRATION: No structured information extracted from message")
                
        except Exception as e:
            logger.error(f"MEMORY_INTEGRATION: Error extracting and saving user information: {e}")
            import traceback
            logger.error(f"MEMORY_INTEGRATION: Traceback: {traceback.format_exc()}")

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
    logger.info(f"MEMORY_INTEGRATION: Enriching prompt with memory for session {session_id}, user {user_id}")
    logger.info(f"MEMORY_INTEGRATION: User message: '{user_message[:50]}...'")
    
    memory_manager = get_memory_manager()
    if not memory_manager:
        logger.warning("MEMORY_INTEGRATION: Cannot enrich prompt - memory manager not initialized")
        return conversation_history or []
    
    # Start with the provided history or empty list
    enhanced_history = conversation_history.copy() if conversation_history else []
    history_length = len(enhanced_history)
    logger.info(f"MEMORY_INTEGRATION: Starting with {history_length} history messages")
    
    try:
        # Rewrite the query if it might be a follow-up question
        search_query = user_message
        if conversation_history and len(conversation_history) > 1:
            logger.info(f"MEMORY_INTEGRATION: Attempting to rewrite possible follow-up query")
            try:
                rewritten_query = memory_manager.rewrite_query(conversation_history, user_message)
                # Only use rewritten query if it's significantly different
                if rewritten_query and len(rewritten_query) > len(user_message) * 1.2:
                    search_query = rewritten_query
                    logger.info(f"MEMORY_INTEGRATION: Rewrote query: '{user_message[:30]}...' -> '{rewritten_query[:30]}...'")
                else:
                    logger.info(f"MEMORY_INTEGRATION: No significant query rewrite needed")
            except Exception as rewrite_error:
                logger.error(f"MEMORY_INTEGRATION: Error rewriting query: {rewrite_error}")
        
        # Retrieve relevant memory
        logger.info(f"MEMORY_INTEGRATION: Retrieving short-term memory")
        short_term = memory_manager.retrieve_short_term_memory(session_id, user_id, search_query)
        short_term_count = len(short_term) if short_term else 0
        logger.info(f"MEMORY_INTEGRATION: Found {short_term_count} relevant short-term memories")
        
        logger.info(f"MEMORY_INTEGRATION: Retrieving long-term memory")
        long_term = memory_manager.retrieve_long_term_memory(user_id, search_query)
        
        # Check what we got from long-term memory
        facts_count = len(long_term.get('matching_facts', {}))
        prefs_count = len(long_term.get('similar_preferences', []))
        logger.info(f"MEMORY_INTEGRATION: Found {facts_count} facts and {prefs_count} preferences in long-term memory")
        
        # Format long-term memory as context message if we have relevant information
        if long_term.get('matching_facts') or long_term.get('similar_preferences'):
            facts = long_term.get('matching_facts', {})
            preferences = [p.get('text') for p in long_term.get('similar_preferences', [])]
            
            if facts or preferences:
                context_parts = []
                
                if facts:
                    # Filter out metadata fields
                    filtered_facts = {k: v for k, v in facts.items() 
                                     if k not in ('created_at', 'updated_at')}
                    
                    if filtered_facts:
                        facts_str = ", ".join([f"{k}: {v}" for k, v in filtered_facts.items()])
                        context_parts.append(f"User facts: {facts_str}")
                        logger.info(f"MEMORY_INTEGRATION: Added {len(filtered_facts)} user facts to context")
                
                if preferences:
                    # Limit to top 3 preferences
                    top_prefs = preferences[:3]
                    prefs_str = ", ".join(top_prefs)
                    context_parts.append(f"User preferences: {prefs_str}")
                    logger.info(f"MEMORY_INTEGRATION: Added {len(top_prefs)} user preferences to context")
                
                if context_parts:
                    context_message = {
                        "role": "system",
                        "content": "Relevant user information:\n" + "\n".join(context_parts)
                    }
                    enhanced_history.insert(0, context_message)
                    logger.info("MEMORY_INTEGRATION: Added long-term memory context message")
        
        # Potentially add relevant past messages that aren't in the recent history
        if short_term:
            # Convert history to set of content strings for easy comparison
            existing_content = {msg.get('content', '') for msg in enhanced_history}
            logger.debug(f"MEMORY_INTEGRATION: Found {len(existing_content)} unique existing messages")
            
            # Find relevant messages not already in history
            relevant_msgs = []
            for msg in short_term:
                content = msg.get('content', '')
                if content and content not in existing_content:
                    relevant_msgs.append({
                        "role": msg.get('role'),
                        "content": content
                    })
            
            relevant_count = len(relevant_msgs)
            logger.info(f"MEMORY_INTEGRATION: Found {relevant_count} new relevant messages to add")
            
            # If we found relevant messages, add them with a marker
            if relevant_msgs:
                enhanced_history.insert(0, {
                    "role": "system",
                    "content": "The following are relevant messages from your previous conversation:"
                })
                enhanced_history[1:1] = relevant_msgs
                logger.info(f"MEMORY_INTEGRATION: Added {len(relevant_msgs)} relevant messages with header")
        
        # Log the final result
        final_length = len(enhanced_history)
        added_messages = final_length - history_length
        
        if added_messages > 0:
            logger.info(f"MEMORY_INTEGRATION: Successfully enriched prompt with {added_messages} additional messages")
        else:
            logger.info(f"MEMORY_INTEGRATION: No additional context was added from memory")
            
        return enhanced_history
        
    except Exception as e:
        logger.error(f"MEMORY_INTEGRATION: Error enriching prompt with memory: {e}")
        import traceback
        logger.error(f"MEMORY_INTEGRATION: Traceback: {traceback.format_exc()}")
        return conversation_history or []