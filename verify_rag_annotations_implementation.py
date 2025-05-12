"""
Script to verify the implementation of OpenRouter annotations for RAG context persistence.
This feature ensures that document context is maintained across conversation turns.
"""

import logging
import os
import sys
import json
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('rag_annotations_check.log')
    ]
)
logger = logging.getLogger('rag_annotations_check')

def check_message_annotations_column():
    """
    Check if the Message table has an annotations column that can store 
    OpenRouter annotations for context persistence.
    """
    try:
        # Import Flask app and models
        from app import app, db
        from models import Message
        
        with app.app_context():
            # Check if the Message model has an annotations attribute
            if not hasattr(Message, 'annotations'):
                logger.error("Message model does not have an 'annotations' attribute!")
                return False
                
            # Check if we can query for messages with annotations
            try:
                # Try to query for messages with non-null annotations
                query = Message.query.filter(Message.annotations.isnot(None))
                
                # Get count of messages with annotations
                count = query.count()
                logger.info(f"Found {count} messages with annotations")
                
                # Look at a few example annotations if available
                if count > 0:
                    examples = query.limit(3).all()
                    logger.info("Example annotations:")
                    for i, msg in enumerate(examples):
                        logger.info(f"Example {i+1}:")
                        logger.info(f"  Message ID: {msg.id}")
                        logger.info(f"  Content (truncated): {msg.content[:100]}...")
                        logger.info(f"  Annotations: {json.dumps(msg.annotations, indent=2)}")
                        
                return True
                
            except Exception as query_error:
                logger.error(f"Error querying annotations: {query_error}")
                return False
                
    except Exception as e:
        logger.error(f"Error checking Message annotations column: {e}")
        return False

def check_annotations_in_requests():
    """
    Check if annotations are included in requests to OpenRouter.
    """
    try:
        # Import the chat function to inspect its implementation
        import app as app_module
        import inspect
        
        # Check if the chat function includes annotations in OpenRouter requests
        chat_source = inspect.getsource(app_module.chat)
        
        # Look for key patterns that indicate annotations handling
        annotations_patterns = [
            "annotations",
            "last_message.annotations",
            "include_annotations",
            "message.annotations"
        ]
        
        matches = []
        for pattern in annotations_patterns:
            if pattern in chat_source:
                matches.append(pattern)
                
        if matches:
            logger.info(f"Found annotations references in chat function: {matches}")
            return True
        else:
            logger.error("No annotations references found in chat function!")
            return False
            
    except Exception as e:
        logger.error(f"Error checking annotations in requests: {e}")
        return False

def check_annotations_processing():
    """
    Check if the application correctly processes annotations from OpenRouter responses.
    """
    try:
        # Look at how Messages are created and saved
        import app as app_module
        import inspect
        
        # Check save_message_with_memory function if it exists
        if hasattr(app_module, 'save_message_with_memory'):
            save_func_source = inspect.getsource(app_module.save_message_with_memory)
            
            # Look for patterns that indicate annotations are saved
            save_annotations_patterns = [
                "annotations",
                "response.get('annotations')",
                "message.annotations"
            ]
            
            save_matches = []
            for pattern in save_annotations_patterns:
                if pattern in save_func_source:
                    save_matches.append(pattern)
                    
            if save_matches:
                logger.info(f"Found annotations handling in save_message_with_memory: {save_matches}")
                return True
            else:
                logger.warning("No annotations handling found in save_message_with_memory")
                return False
        else:
            logger.warning("No save_message_with_memory function found")
            
        # Also check the chat function for annotations processing
        chat_source = inspect.getsource(app_module.chat)
        
        process_patterns = [
            "annotations",
            "response.get('annotations')",
            "message.annotations =",
            "extract_annotations"
        ]
        
        process_matches = []
        for pattern in process_patterns:
            if pattern in chat_source:
                process_matches.append(pattern)
                
        if process_matches:
            logger.info(f"Found annotations processing in chat function: {process_matches}")
            return True
        else:
            logger.warning("No annotations processing found in chat function")
            return False
            
    except Exception as e:
        logger.error(f"Error checking annotations processing: {e}")
        return False

def check_annotations_usage():
    """
    Check if the application correctly uses stored annotations for context persistence.
    """
    try:
        # Look at how previous annotations are included in new requests
        import app as app_module
        import inspect
        
        # Check the chat function for reusing annotations
        chat_source = inspect.getsource(app_module.chat)
        
        reuse_patterns = [
            "last_message.annotations",
            "previous_annotations",
            "include_annotations"
        ]
        
        reuse_matches = []
        for pattern in reuse_patterns:
            if pattern in chat_source:
                reuse_matches.append(pattern)
                
        if reuse_matches:
            logger.info(f"Found annotations reuse in chat function: {reuse_matches}")
            return True
        else:
            logger.warning("No annotations reuse found in chat function")
            return False
            
    except Exception as e:
        logger.error(f"Error checking annotations usage: {e}")
        return False

def main():
    """
    Run all verification checks.
    """
    logger.info("=== Starting RAG Annotations Implementation Check ===")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    column_check = check_message_annotations_column()
    logger.info(f"Message annotations column check: {'PASSED' if column_check else 'FAILED'}")
    
    request_check = check_annotations_in_requests()
    logger.info(f"Annotations in requests check: {'PASSED' if request_check else 'FAILED'}")
    
    processing_check = check_annotations_processing()
    logger.info(f"Annotations processing check: {'PASSED' if processing_check else 'FAILED'}")
    
    usage_check = check_annotations_usage()
    logger.info(f"Annotations usage for context persistence check: {'PASSED' if usage_check else 'FAILED'}")
    
    logger.info("=== RAG Annotations Implementation Check Complete ===")
    logger.info(f"Overall status: {'PASSED' if (column_check and request_check and processing_check and usage_check) else 'FAILED'}")
    
    return 0 if (column_check and request_check and processing_check and usage_check) else 1

if __name__ == "__main__":
    sys.exit(main())