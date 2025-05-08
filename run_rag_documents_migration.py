#!/usr/bin/env python3
"""
Run the RAG documents migration to add rag_documents column to the Message model.
"""
import os
import logging
from flask import Flask
import migrations_rag_documents

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Execute the migration"""
    logger.info("Starting RAG documents migration")
    
    # Import Flask app to ensure proper context
    from app import app
    
    # Run the migration within app context
    with app.app_context():
        success = migrations_rag_documents.run_migration()
        
        if success:
            logger.info("RAG documents migration completed successfully")
        else:
            logger.error("RAG documents migration failed")
        
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)