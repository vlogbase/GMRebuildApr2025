"""
Database utility functions for common operations with proper app context handling
"""

import logging
from typing import Optional, List, Dict, Any, Union, Type

from ensure_app_context import with_app_context
from app import db
from models import Message, Conversation, User

logger = logging.getLogger(__name__)

@with_app_context
def get_message_by_id(message_id: int) -> Optional[Message]:
    """
    Get a message by ID with proper app context handling
    
    Args:
        message_id: The ID of the message to retrieve
        
    Returns:
        Message instance or None if not found
    """
    return Message.query.get(message_id)

@with_app_context
def get_conversation_by_id(conversation_id: int) -> Optional[Conversation]:
    """
    Get a conversation by ID with proper app context handling
    
    Args:
        conversation_id: The ID of the conversation to retrieve
        
    Returns:
        Conversation instance or None if not found
    """
    return Conversation.query.get(conversation_id)

@with_app_context
def get_messages_for_conversation(conversation_id: int) -> List[Message]:
    """
    Get all messages for a conversation with proper app context handling
    
    Args:
        conversation_id: The ID of the conversation
        
    Returns:
        List of Message instances
    """
    return Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()

@with_app_context(error_handler=lambda e: logger.error(f"Error saving message: {e}"))
def save_message(conversation_id: int, role: str, content: str, 
                 image_url: Optional[str] = None, 
                 pdf_url: Optional[str] = None,
                 pdf_filename: Optional[str] = None) -> Optional[Message]:
    """
    Save a message with proper app context handling and error handling
    
    Args:
        conversation_id: The ID of the conversation
        role: The role of the message sender ('user' or 'assistant')
        content: The text content of the message
        image_url: Optional image URL for multimodal messages
        pdf_url: Optional PDF URL for document messages
        pdf_filename: Optional PDF filename
        
    Returns:
        Saved Message instance or None if error occurred
    """
    try:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            image_url=image_url,
            pdf_url=pdf_url,
            pdf_filename=pdf_filename
        )
        db.session.add(message)
        db.session.commit()
        logger.info(f"Successfully saved {role} message {message.id} to conversation {conversation_id}")
        return message
    except Exception as e:
        logger.error(f"Error creating message: {e}")
        db.session.rollback()
        return None