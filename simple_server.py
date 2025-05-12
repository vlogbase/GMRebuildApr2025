"""
Simple Flask server to run the application.
This bypasses the circular import issues by directly importing the app object.
"""

import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_server():
    """Run the Flask server"""
    try:
        # Import the app directly - we resolve circular imports by importing 
        # the app object after it has been fully defined in app.py
        from app import app
        
        # Determine port
        port = int(os.environ.get("PORT", 5000))
        
        # Run the application
        logger.info(f"Starting Flask application on port {port}")
        app.run(host="0.0.0.0", port=port, debug=True)
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_server()