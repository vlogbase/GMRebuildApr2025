"""
Test workflow for the conversation tracking fixes

This script starts the Flask application to test:
1. The creation of new conversations when "New Chat" is clicked
2. Proper tracking of conversations in the sidebar
3. Initial creation of conversations on page load
"""

import os
import logging
from app import app

def run():
    """
    Run the Flask application with the conversation tracking fixes
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('conversation_fix_test.log')
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Flask server to test conversation tracking fixes...")
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    run()