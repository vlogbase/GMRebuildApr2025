"""
Test workflow specifically for testing Google login redirection
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application to test login functionality
    """
    try:
        logger.info("Starting Flask server for login testing")
        
        # Add parent directory to path to be able to import app
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # Import the app here to ensure it's initialized in this process
        from app import app
        
        # Start the server
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"Starting Flask application on port {port}")
        logger.info("Visit the /info page to test login redirection")
        app.run(host="0.0.0.0", port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()