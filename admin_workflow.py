"""
Simple Flask server workflow for GloriaMundo Admin Panel

This workflow now includes the conversation tracking fixes to test:
1. The creation of new conversations when "New Chat" is clicked
2. Proper tracking of conversations in the sidebar 
3. Initial creation of conversations on page load
"""

import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from app import app  # Import the Flask app from app.py

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('admin_workflow.log')
    ]
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting GloriaMundo Admin Panel Server...")
    
    # Get port from environment variable or use 5000 as default
    port = int(os.environ.get("PORT", 5000))
    
    # Run the Flask application
    app.run(host="0.0.0.0", port=port, debug=True)