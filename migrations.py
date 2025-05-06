import logging
from app import app, db
import sqlalchemy as sa

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """
    Apply database migrations to add new columns to Conversation and Message tables.
    
    This function should be run in the Flask application context.
    """
    logger.info("Starting database migrations...")
    
    # Use raw SQL to perform the migrations
    conn = db.engine.connect()
    
    try:
        # Check if share_id column exists in conversation table
        result = conn.execute(sa.text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'conversation' AND column_name = 'share_id'"
        ))
        if not result.fetchone():
            logger.info("Adding share_id to conversation table")
            conn.execute(sa.text("ALTER TABLE conversation ADD COLUMN share_id VARCHAR(64)"))
            conn.execute(sa.text("CREATE INDEX ix_conversation_share_id ON conversation (share_id)"))
        else:
            logger.info("share_id column already exists in conversation table")
        
        # Check and add columns to the message table
        
        # Check rating column
        result = conn.execute(sa.text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'message' AND column_name = 'rating'"
        ))
        if not result.fetchone():
            logger.info("Adding rating column to message table")
            conn.execute(sa.text("ALTER TABLE message ADD COLUMN rating INTEGER"))
        else:
            logger.info("rating column already exists in message table")
        
        # Check model_id_used column
        result = conn.execute(sa.text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'message' AND column_name = 'model_id_used'"
        ))
        if not result.fetchone():
            logger.info("Adding model_id_used column to message table")
            conn.execute(sa.text("ALTER TABLE message ADD COLUMN model_id_used VARCHAR(64)"))
        else:
            logger.info("model_id_used column already exists in message table")
        
        # Check prompt_tokens column
        result = conn.execute(sa.text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'message' AND column_name = 'prompt_tokens'"
        ))
        if not result.fetchone():
            logger.info("Adding prompt_tokens column to message table")
            conn.execute(sa.text("ALTER TABLE message ADD COLUMN prompt_tokens INTEGER"))
        else:
            logger.info("prompt_tokens column already exists in message table")
        
        # Check completion_tokens column
        result = conn.execute(sa.text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'message' AND column_name = 'completion_tokens'"
        ))
        if not result.fetchone():
            logger.info("Adding completion_tokens column to message table")
            conn.execute(sa.text("ALTER TABLE message ADD COLUMN completion_tokens INTEGER"))
        else:
            logger.info("completion_tokens column already exists in message table")
        
        # Commit the transaction
        conn.commit()
        logger.info("Database migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Error performing database migrations: {e}")
        # Rollback in case of error
        conn.rollback()
        raise
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    with app.app_context():
        migrate_database()