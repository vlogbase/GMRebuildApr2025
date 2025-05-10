"""
Migration script to set up conversation document relations.

This script sets up the necessary schema for per-conversation document tracking.
"""
import os
import sys
import logging
from datetime import datetime

import pymongo
from bson.objectid import ObjectId
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('migrations_conversation_docs')

# Get the database URL from environment variables
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    logger.error("DATABASE_URL environment variable not set")
    sys.exit(1)

# Create the SQLAlchemy engine and session
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

# Get MongoDB URI from environment variables (try both possible variable names)
mongodb_uri = os.environ.get('MONGODB_ATLAS_URI', os.environ.get('MONGODB_URI'))
# Note: We don't fail if MongoDB URI is not available, we'll just skip document migration

def check_conversation_document_table():
    """Check if the ConversationDocument table exists."""
    try:
        # Create a new connection to avoid transaction issues
        conn = engine.connect()
        result = conn.execute(text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='conversation_document')"))
        exists = result.scalar()
        conn.close()
        logger.info(f"ConversationDocument table exists: {exists}")
        return exists
    except Exception as e:
        logger.info(f"Error checking ConversationDocument table: {e}")
        # Make sure to roll back any pending transaction
        session.rollback()
        return False

def create_conversation_document_table():
    """Create the ConversationDocument table if it doesn't exist."""
    # Create a new connection for this operation
    conn = None
    try:
        conn = engine.connect()
        # Begin a transaction
        trans = conn.begin()
        # Create the table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS conversation_document (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER NOT NULL,
            document_identifier VARCHAR(512) NOT NULL,
            original_filename VARCHAR(256) NOT NULL,
            is_context_active BOOLEAN NOT NULL DEFAULT TRUE,
            upload_timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            FOREIGN KEY (conversation_id) REFERENCES conversation (id) ON DELETE CASCADE
        )
        """))
        # Commit the transaction
        trans.commit()
        logger.info("ConversationDocument table created successfully")
        return True
    except Exception as e:
        # Roll back transaction if there was an error
        if conn and conn.in_transaction():
            trans.rollback()
        logger.error(f"Error creating ConversationDocument table: {e}")
        return False
    finally:
        # Close connection
        if conn:
            conn.close()

def create_index_on_conversation_document():
    """Create indexes on the ConversationDocument table."""
    # Create a new connection for this operation
    conn = None
    try:
        conn = engine.connect()
        # Begin a transaction
        trans = conn.begin()
        
        # Create first index
        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_conversation_document_conversation_id
        ON conversation_document (conversation_id)
        """))
        
        # Create second index
        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_conversation_document_document_identifier
        ON conversation_document (document_identifier)
        """))
        
        # Commit the transaction
        trans.commit()
        logger.info("Indexes created on ConversationDocument table")
        return True
    except Exception as e:
        # Roll back transaction if there was an error
        if conn and conn.in_transaction():
            trans.rollback()
        logger.error(f"Error creating indexes on ConversationDocument table: {e}")
        return False
    finally:
        # Close connection
        if conn:
            conn.close()

def connect_to_mongodb():
    """Connect to MongoDB and return the client and required collections."""
    if not mongodb_uri:
        logger.warning("MongoDB URI not available. Skipping MongoDB connection.")
        return None, None
        
    try:
        client = pymongo.MongoClient(mongodb_uri)
        db = client.get_database('memory')
        
        # Get collections
        documents_collection = db.get_collection('documents')
        
        # Check if collections exist
        if documents_collection is None:
            logger.warning("MongoDB 'documents' collection not found")
            return None, None
            
        return client, documents_collection
    except Exception as e:
        logger.warning(f"Error connecting to MongoDB: {e}")
        return None, None

def migrate_existing_documents():
    """
    Migrate existing documents from MongoDB to the SQL database.
    For each document in MongoDB, create a ConversationDocument record for the owner's conversations.
    This step is optional and the migration will succeed even if MongoDB is unavailable.
    """
    try:
        # Connect to MongoDB
        mongo_client, documents_collection = connect_to_mongodb()
        # Proper way to check if MongoDB collections are None
        if mongo_client is None or documents_collection is None:
            logger.warning("MongoDB connection not available. Skipping document migration.")
            return True  # Return True to continue with the migration
            
        # Get all documents
        documents = list(documents_collection.find({}))
        logger.info(f"Found {len(documents)} documents in MongoDB")
        
        # Track migration statistics
        success_count = 0
        skipped_count = 0
        error_count = 0
        
        # For each document, create ConversationDocument records
        for doc in documents:
            doc_id = str(doc.get('_id', 'unknown'))
            user_id = doc.get('user_id')
            
            # Skip documents without user_id
            if not user_id:
                logger.info(f"Skipping document {doc_id}: No user_id found")
                skipped_count += 1
                continue
                
            # Process this document
            try:
                # Handle temporary user IDs that are string UUIDs
                if isinstance(user_id, str) and user_id.startswith('temp_'):
                    logger.info(f"Skipping temporary user ID: {user_id} for document {doc_id}")
                    skipped_count += 1
                    continue
                
                # Try to convert user_id to an integer
                try:
                    user_id_int = int(user_id)
                except ValueError:
                    logger.warning(f"Could not convert user_id '{user_id}' to integer for document {doc_id}, skipping")
                    skipped_count += 1
                    continue
                
                # Get all conversations for this user
                conversations = session.execute(
                    text("SELECT id FROM conversation WHERE user_id = :user_id"),
                    {"user_id": user_id_int}
                ).fetchall()
                
                if not conversations:
                    logger.info(f"No conversations found for user {user_id}, skipping document {doc_id}")
                    skipped_count += 1
                    continue
                
                # Successfully added to at least one conversation
                doc_success = False
                    
                for conv in conversations:
                    conversation_id = conv[0]
                    
                    # Check if record already exists
                    existing = session.execute(
                        text("""
                        SELECT 1 FROM conversation_document 
                        WHERE conversation_id = :conversation_id 
                        AND document_identifier = :doc_id
                        """),
                        {
                            "conversation_id": conversation_id,
                            "doc_id": doc_id
                        }
                    ).fetchone()
                    
                    if existing:
                        logger.debug(f"Document {doc_id} already exists for conversation {conversation_id}, skipping")
                        continue
                        
                    # Create a new ConversationDocument record
                    try:
                        session.execute(
                            text("""
                            INSERT INTO conversation_document 
                            (conversation_id, document_identifier, original_filename, is_context_active, upload_timestamp)
                            VALUES (:conversation_id, :doc_id, :filename, TRUE, :timestamp)
                            """),
                            {
                                "conversation_id": conversation_id,
                                "doc_id": doc_id,
                                "filename": doc.get('filename', 'Unknown Document'),
                                "timestamp": doc.get('upload_timestamp', datetime.utcnow())
                            }
                        )
                        doc_success = True
                        logger.debug(f"Created ConversationDocument record for document {doc_id} and conversation {conversation_id}")
                    except Exception as insert_error:
                        logger.error(f"Error inserting document {doc_id} for conversation {conversation_id}: {insert_error}")
                
                if doc_success:
                    success_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                logger.error(f"Error migrating document {doc_id} for user {user_id}: {e}")
                error_count += 1
                continue
                
        logger.info(f"Document migration summary: {success_count} successful, {skipped_count} skipped, {error_count} errors")
                
        # Commit all changes
        session.commit()
        logger.info("Document migration completed successfully")
        return True
            
    except Exception as e:
        session.rollback()
        logger.error(f"Error migrating documents: {e}")
        return False
    finally:
        if 'mongo_client' in locals() and mongo_client:
            mongo_client.close()

def run_migration():
    """Run the migration process."""
    logger.info("Starting conversation document migration")
    
    # Check if table exists
    if check_conversation_document_table():
        logger.info("ConversationDocument table already exists")
    else:
        logger.info("Creating ConversationDocument table")
        if not create_conversation_document_table():
            logger.error("Failed to create ConversationDocument table")
            return False
            
    # Create indexes
    if not create_index_on_conversation_document():
        logger.error("Failed to create indexes on ConversationDocument table")
        return False
        
    # Try to migrate existing documents (optional step)
    try:
        migrate_existing_documents()
    except Exception as e:
        logger.warning(f"Optional document migration had issues: {e}")
        logger.warning("Continuing with migration as document linking is optional")
        
    logger.info("Conversation document schema migration completed successfully")
    return True

if __name__ == "__main__":
    success = run_migration()
    if success:
        logger.info("Migration completed successfully")
        sys.exit(0)
    else:
        logger.error("Migration failed")
        sys.exit(1)