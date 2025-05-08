#!/usr/bin/env python3
"""
Test script for the enhanced chat interface UI features:
1. Dynamic textarea auto-height
2. Message truncation for long messages with "Show more"/"Show less" toggle
3. Visual indicators for RAG document references
"""
import os
import logging
from flask import Flask
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Start the Flask application for testing the chat UI"""
    logger.info("Starting chat UI test application")
    
    # Run the Flask app with debug enabled
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()