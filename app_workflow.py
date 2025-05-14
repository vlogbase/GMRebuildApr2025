"""
Simple Flask server workflow for GloriaMundo Chatbot
"""
import os
from app import app

def run():
    """
    Run the Flask application for testing
    """
    # Get the port from environment variable or use default
    port = os.environ.get('PORT', 5000)
    
    # Run the app with host 0.0.0.0 to make it accessible externally
    app.run(host='0.0.0.0', port=int(port), debug=True)

if __name__ == '__main__':
    run()