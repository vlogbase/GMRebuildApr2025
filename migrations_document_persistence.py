"""
Migration script to add the DocumentReference model for document persistence in chat sessions.
This allows documents to be attached to conversations and remain visible throughout the session.
"""
import os
import logging
import sys
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, inspect
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the database URL from the environment variables
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    logger.error("DATABASE_URL not found in environment variables")
    sys.exit(1)

# Create the base class for declarative models
Base = declarative_base()

# Define the Conversation model minimal schema (only what we need for references)
class Conversation(Base):
    __tablename__ = 'conversation'
    
    id = Column(Integer, primary_key=True)
    # We don't need to define all fields, just the primary key for foreign key reference

# Define the DocumentReference model to match our current model definition
class DocumentReference(Base):
    __tablename__ = 'document_reference'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversation.id'), nullable=False)
    document_type = Column(String(20), nullable=False)  # 'image', 'pdf', etc.
    document_url = Column(Text, nullable=False)  # URL or data URL for the document
    document_name = Column(String(255), nullable=True)  # Name of the document
    is_active = Column(Boolean, default=True)  # Whether this document is currently in context
    created_at = Column(DateTime, default=datetime.utcnow)

def run_migrations():
    """
    Run the migration to create the DocumentReference table
    and add any other necessary changes to support document persistence.
    """
    try:
        # Create the database engine
        engine = create_engine(db_url)
        
        # Check if the table already exists
        if not inspect(engine).has_table('document_reference'):
            # Create the table
            logger.info("Creating document_reference table...")
            Base.metadata.create_all(engine, tables=[DocumentReference.__table__])
            logger.info("document_reference table created successfully.")
            
            # Create a session
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Close the session
            session.close()
            
            return True
        else:
            logger.info("document_reference table already exists.")
            return True
    
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return False

if __name__ == "__main__":
    # Run the migrations when the script is executed directly
    success = run_migrations()
    if success:
        logger.info("Document persistence migrations completed successfully!")
    else:
        logger.error("Document persistence migrations failed.")
        sys.exit(1)