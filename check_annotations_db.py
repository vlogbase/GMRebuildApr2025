"""
Script to check for existing annotations in the database
"""
import os
import sys
import json
import logging
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_annotations():
    """
    Check for existing annotations in the database.
    """
    try:
        # Get database URL from environment
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            return False
            
        # Create engine
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Check if the annotations column exists
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'message' AND column_name = 'annotations'"
            ))
            
            if not result.fetchone():
                logger.error("annotations column does not exist in message table")
                return False
            
            logger.info("annotations column exists in message table")
            
            # Check for messages with annotations
            result = conn.execute(text(
                "SELECT id, role, conversation_id, annotations FROM message "
                "WHERE annotations IS NOT NULL "
                "LIMIT 10"
            ))
            
            rows = result.fetchall()
            if not rows:
                logger.info("No messages found with annotations")
            else:
                logger.info(f"Found {len(rows)} messages with annotations:")
                for row in rows:
                    message_id, role, conversation_id, annotations = row
                    logger.info(f"Message ID: {message_id}, Role: {role}, Conversation ID: {conversation_id}")
                    logger.info(f"Annotations: {json.dumps(annotations, indent=2)}")
            
            # Get total message count
            result = conn.execute(text("SELECT COUNT(*) FROM message"))
            total_messages = result.fetchone()[0]
            logger.info(f"Total messages in database: {total_messages}")
            
            # Get total conversations count
            result = conn.execute(text("SELECT COUNT(*) FROM conversation"))
            total_conversations = result.fetchone()[0]
            logger.info(f"Total conversations in database: {total_conversations}")
            
            return True
                
    except Exception as e:
        logger.error(f"Error checking annotations: {e}")
        return False

if __name__ == "__main__":
    logger.info("Checking for annotations in the database...")
    success = check_annotations()
    if success:
        logger.info("Successfully checked annotations")
    else:
        logger.error("Failed to check annotations")
        sys.exit(1)