"""
Simple Flask server workflow for GloriaMundo Chatbot Application

This workflow runs the main Flask application with all features enabled:
- Chat interface
- Model fallback confirmation
- User settings
- Document management
- Payment processing
"""
import os
import logging
from app import app

def run():
    """
    Run the Flask application with debugging and appropriate host/port settings
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='app_workflow.log'
    )
    
    # Set the host to make the app accessible
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    run()