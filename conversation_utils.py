"""
Conversation utilities for sharing, forking, and cleanup functionality
"""
import logging
from database import db
from models import Conversation, Message
from datetime import datetime

logger = logging.getLogger(__name__)

def fork_conversation(original_conversation, new_owner):
    """
    Create a copy of a conversation for a new user.
    
    This allows users to "import and continue" shared conversations,
    creating their own copy that they can modify and extend.
    
    Args:
        original_conversation (Conversation): The conversation to copy
        new_owner (User): The user who will own the new conversation
        
    Returns:
        Conversation: The newly created conversation copy
    """
    try:
        # Create a new conversation record for the new owner
        new_conversation = Conversation(
            user_id=new_owner.id,
            title=f"Copy of: {original_conversation.title}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        
        # Add and flush to get the new conversation ID
        db.session.add(new_conversation)
        db.session.flush()
        
        logger.info(f"Created new conversation {new_conversation.id} as copy of {original_conversation.id} for user {new_owner.id}")
        
        # Get all messages from the original conversation
        original_messages = Message.query.filter_by(
            conversation_id=original_conversation.id
        ).order_by(Message.created_at.asc()).all()
        
        logger.info(f"Found {len(original_messages)} messages to copy")
        
        # Copy each message to the new conversation
        for original_msg in original_messages:
            new_message = Message(
                conversation_id=new_conversation.id,
                role=original_msg.role,
                content=original_msg.content,
                model=original_msg.model,
                model_id_used=original_msg.model_id_used,
                prompt_tokens=original_msg.prompt_tokens,
                completion_tokens=original_msg.completion_tokens,
                image_url=original_msg.image_url,
                pdf_url=original_msg.pdf_url,
                pdf_filename=original_msg.pdf_filename,
                created_at=original_msg.created_at,  # Preserve original timestamps
                rating=None  # Reset ratings for the new copy
            )
            db.session.add(new_message)
        
        # Commit all changes
        db.session.commit()
        
        logger.info(f"Successfully forked conversation {original_conversation.id} to new conversation {new_conversation.id}")
        return new_conversation
        
    except Exception as e:
        logger.error(f"Error forking conversation {original_conversation.id}: {e}")
        db.session.rollback()
        raise


def cleanup_empty_conversations(db, Message, Conversation, user_id):
    """
    Clean up empty conversations (conversations with no messages) for a specific user.
    
    Args:
        db: Database session
        Message: Message model class
        Conversation: Conversation model class
        user_id: ID of the user whose empty conversations to clean up
        
    Returns:
        int: Number of conversations cleaned up
    """
    try:
        # Find conversations that have no messages
        empty_conversations = db.session.query(Conversation).filter(
            Conversation.user_id == user_id,
            ~db.session.query(Message).filter(
                Message.conversation_id == Conversation.id
            ).exists()
        ).all()
        
        cleaned_count = len(empty_conversations)
        
        # Delete empty conversations
        for conversation in empty_conversations:
            db.session.delete(conversation)
            
        db.session.commit()
        
        logger.info(f"Cleaned up {cleaned_count} empty conversations for user {user_id}")
        return cleaned_count
        
    except Exception as e:
        logger.error(f"Error cleaning up empty conversations for user {user_id}: {e}")
        db.session.rollback()
        raise


def is_conversation_empty(db, Message, conversation_id):
    """
    Check if a conversation has no messages.
    
    Args:
        db: Database session
        Message: Message model class
        conversation_id: ID of the conversation to check
        
    Returns:
        bool: True if conversation is empty, False otherwise
    """
    try:
        message_count = db.session.query(Message).filter_by(
            conversation_id=conversation_id
        ).count()
        
        return message_count == 0
        
    except Exception as e:
        logger.error(f"Error checking if conversation {conversation_id} is empty: {e}")
        raise


def delete_conversation_if_empty(db, Message, Conversation, conversation_id, user_id):
    """
    Delete a conversation if it has no messages and belongs to the specified user.
    
    Args:
        db: Database session
        Message: Message model class
        Conversation: Conversation model class
        conversation_id: ID of the conversation to check and delete
        user_id: ID of the user (for security verification)
        
    Returns:
        bool: True if conversation was deleted, False otherwise
    """
    try:
        # Get the conversation and verify ownership
        conversation = db.session.query(Conversation).filter_by(
            id=conversation_id, 
            user_id=user_id
        ).first()
        
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found or doesn't belong to user {user_id}")
            return False
            
        # Check if conversation is empty
        if is_conversation_empty(db, Message, conversation_id):
            db.session.delete(conversation)
            db.session.commit()
            logger.info(f"Deleted empty conversation {conversation_id} for user {user_id}")
            return True
        else:
            logger.info(f"Conversation {conversation_id} is not empty, not deleting")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id} if empty: {e}")
        db.session.rollback()
        raise