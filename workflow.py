"""
Main workflow for running the GloriaMundo Flask application.
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
    Run the Flask application
    """
    try:
        logger.info("Starting Flask server for GloriaMundo")
        
        # Run the Flask application
        # Import the app here to ensure it's initialized in this process
        from app import app
        
        # Start the server
        port = int(os.environ.get("PORT", 3000))
        logger.info(f"Starting Flask application on port {port}")
        app.run(host="0.0.0.0", port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()