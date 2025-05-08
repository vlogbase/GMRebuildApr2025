#!/usr/bin/env python3
"""
Migration script to add rag_documents column to the Message model.
This adds support for storing document names used in RAG responses.
"""
import os
import sys
import logging
from sqlalchemy import Column, Text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migration():
    """Execute the database migration to add rag_documents column"""
    try:
        from app import db
        from models import Message
        
        # Check if column already exists to avoid errors
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('message')]
        
        if 'rag_documents' not in columns:
            logger.info("Adding 'rag_documents' column to Message model")
            
            # Add the column - using SQLAlchemy Core for compatibility
            from sqlalchemy import text
            db.session.execute(text('ALTER TABLE message ADD COLUMN rag_documents TEXT'))
            logger.info("Successfully added 'rag_documents' column")
        else:
            logger.info("Column 'rag_documents' already exists, no migration needed")
            
        return True
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_migration()
    if not success:
        sys.exit(1)