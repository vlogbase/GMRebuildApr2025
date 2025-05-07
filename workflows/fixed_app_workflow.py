"""
Run the Flask application with fixes for HTTP 400 errors in OpenRouter API integration.
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            "fixed_app_workflow.log", 
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
    ]
)
logger = logging.getLogger(__name__)

def run():
    """Run the Flask application with fixes."""
    try:
        # Add parent directory to path
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Import the app instance
        from app import app
        
        # Set environment variables
        port = int(os.environ.get("PORT", 5000))
        
        logger.info("Starting Flask application with HTTP 400 error fixes...")
        logger.info(f"Server will run on port {port}")
        
        # Start the app
        app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
    except Exception as e:
        logger.exception(f"Error starting Flask application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()