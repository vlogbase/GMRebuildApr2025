"""
Conversation utilities for sharing and forking functionality
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