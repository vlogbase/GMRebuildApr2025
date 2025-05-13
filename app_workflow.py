"""
Simple Flask server workflow for GloriaMundo Chatbot
"""

import os
import logging
from app import app

def run():
    """
    Run the Flask application
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

    # Configure the Flask app
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Start the Flask server
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()