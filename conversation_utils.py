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
    Uses a single efficient query to find empty conversations.
    
    Args:
        db: SQLAlchemy database instance
        Message: Message model class
        Conversation: Conversation model class
        user_id: ID of the user whose conversations should be cleaned up
        
    Returns:
        int: Number of conversations deleted
    """
    try:
        # Find all conversation IDs that have messages (not empty)
        conversations_with_messages = db.session.query(Message.conversation_id)\
            .distinct()\
            .scalar_subquery()  # Use scalar_subquery() to properly handle IN clause
        
        # Find all conversations for the user that don't have any messages
        empty_conversations = Conversation.query\
            .filter(Conversation.user_id == user_id)\
            .filter(Conversation.is_active == True)\
            .filter(~Conversation.id.in_(conversations_with_messages))\
            .all()
        
        deleted_count = len(empty_conversations)
        
        if deleted_count > 0:
            # Permanently delete the empty conversations
            for conversation in empty_conversations:
                db.session.delete(conversation)
                logger.info(f"Deleting empty conversation {conversation.id} for user {user_id}")
            
            # Commit the changes
            db.session.commit()
            logger.info(f"Permanently deleted {deleted_count} empty conversations for user {user_id}")
        
        return deleted_count
    
    except Exception as e:
        logger.error(f"Error cleaning up empty conversations for user {user_id}: {e}")
        db.session.rollback()
        return 0

def delete_conversation_if_empty(db, Message, Conversation, conversation_id):
    """
    Delete a specific conversation if it has no messages.
    Performs hard delete to permanently remove empty conversations.
    
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
            # Permanently delete the conversation (hard delete)
            db.session.delete(conversation)
            db.session.commit()
            logger.info(f"Permanently deleted empty conversation {conversation_id}")
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error deleting empty conversation {conversation_id}: {e}")
        db.session.rollback()
        return False