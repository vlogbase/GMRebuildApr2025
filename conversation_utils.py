"""
Conversation Utilities for GloriaMundo

Functions for managing conversation lifecycle, including cleanup of empty conversations
"""
import logging
from sqlalchemy.exc import NoResultFound
from flask import current_app

# Set up logging
logger = logging.getLogger(__name__)

def is_conversation_empty(db, Message, conversation_id):
    """
    Check if a conversation has any messages.
    
    Args:
        db: SQLAlchemy database instance
        Message: Message model class
        conversation_id: ID of the conversation to check
        
    Returns:
        bool: True if the conversation has no messages, False otherwise
    """
    try:
        message_count = Message.query.filter_by(conversation_id=conversation_id).count()
        return message_count == 0
    except Exception as e:
        logger.error(f"Error checking if conversation {conversation_id} is empty: {e}")
        # Default to False (not empty) to prevent accidental deletion
        return False

def cleanup_empty_conversations(db, Message, Conversation, user_id):
    """
    Find and delete all empty conversations for a user.
    
    Args:
        db: SQLAlchemy database instance
        Message: Message model class
        Conversation: Conversation model class
        user_id: ID of the user whose conversations should be cleaned up
        
    Returns:
        int: Number of conversations deleted
    """
    try:
        # Get all active conversations for the user
        conversations = Conversation.query.filter_by(user_id=user_id, is_active=True).all()
        
        deleted_count = 0
        for conversation in conversations:
            # Check if the conversation has any messages
            if is_conversation_empty(db, Message, conversation.id):
                # Delete empty conversation (marking as inactive)
                conversation.is_active = False
                deleted_count += 1
                logger.info(f"Marking empty conversation {conversation.id} as inactive for user {user_id}")
        
        # Commit changes if any conversations were deleted
        if deleted_count > 0:
            db.session.commit()
            logger.info(f"Cleaned up {deleted_count} empty conversations for user {user_id}")
        
        return deleted_count
    
    except Exception as e:
        logger.error(f"Error cleaning up empty conversations for user {user_id}: {e}")
        db.session.rollback()
        return 0

def delete_conversation_if_empty(db, Message, Conversation, conversation_id):
    """
    Delete a specific conversation if it has no messages.
    
    Args:
        db: SQLAlchemy database instance
        Message: Message model class
        Conversation: Conversation model class
        conversation_id: ID of the conversation to check and potentially delete
        
    Returns:
        bool: True if conversation was deleted, False otherwise
    """
    try:
        # Check if conversation exists and is active
        conversation = Conversation.query.filter_by(id=conversation_id, is_active=True).first()
        
        if not conversation:
            logger.warning(f"Cannot delete non-existent or inactive conversation: {conversation_id}")
            return False
        
        # Check if conversation is empty
        if is_conversation_empty(db, Message, conversation_id):
            # Mark conversation as inactive (soft delete)
            conversation.is_active = False
            db.session.commit()
            logger.info(f"Deleted empty conversation {conversation_id}")
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error deleting empty conversation {conversation_id}: {e}")
        db.session.rollback()
        return False