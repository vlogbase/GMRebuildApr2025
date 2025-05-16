"""
A simple workflow to test the mobile message collapsing functionality.
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run():
    """Run the Flask app to test the message collapsing functionality"""
    try:
        logger.info("Starting Flask app for mobile UI message collapse testing...")
        
        # Import the main app
        sys.path.insert(0, os.getcwd())
        from app import app
        
        # Log some information about JS files
        js_path = os.path.join(os.getcwd(), 'static', 'js')
        logger.info(f"JS directory: {js_path}")
        logger.info(f"message-collapse.js exists: {os.path.exists(os.path.join(js_path, 'message-collapse.js'))}")
        
        # Run the app with debug mode enabled
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error running Flask app: {str(e)}")
        raise

if __name__ == "__main__":
    run()