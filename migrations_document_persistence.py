"""
Migrations for document persistence feature.
This script creates the document_reference table and adds the relationship to conversations.
"""
import os
import logging
import sys
import time
from datetime import datetime
from sqlalchemy import text, Column, Integer, String, Text, Boolean, DateTime, ForeignKey

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migrations_document_persistence.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_migrations():
    """
    Run database migrations for document persistence.
    Creates document_reference table if it doesn't exist.
    """
    try:
        logger.info("Starting document persistence migrations")
        
        # Import the app and database
        from app import app, db
        from sqlalchemy import inspect
        
        # Push the application context
        with app.app_context():
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            # Check if document_reference table already exists
            if 'document_reference' not in tables:
                logger.info("Creating document_reference table")
                
                # Create the document_reference table
                with db.engine.connect() as conn:
                    conn.execute(text("""
                    CREATE TABLE document_reference (
                        id SERIAL PRIMARY KEY,
                        conversation_id INTEGER NOT NULL,
                        document_type VARCHAR(20) NOT NULL,
                        document_url TEXT NOT NULL,
                        document_name VARCHAR(255),
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (conversation_id) REFERENCES conversation (id) ON DELETE CASCADE
                    )
                    """))
                    conn.commit()
                
                logger.info("document_reference table created successfully")
            else:
                logger.info("document_reference table already exists, skipping creation")
            
            # Add index to improve query performance
            with db.engine.connect() as conn:
                conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_document_reference_conversation_active 
                ON document_reference (conversation_id, is_active)
                """))
                conn.commit()
            
            logger.info("Document persistence migrations completed successfully")
            return True
    
    except Exception as e:
        logger.error(f"Error during document persistence migrations: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = run_migrations()
    if success:
        print("Document persistence migrations completed successfully")
        sys.exit(0)
    else:
        print("Document persistence migrations failed")
        sys.exit(1)