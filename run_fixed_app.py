"""
Run the Flask application with fixes for HTTP 400 errors in OpenRouter API integration.

This script imports the app instance from app.py and runs it with the correct configuration.
The fixes implemented include:
1. Updated model IDs to match what's available in OpenRouter
2. Robust multimodal content handling
3. Fallback mechanisms for model selection
4. Validation of models before API calls
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
            "app_output.log", 
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run the Flask application."""
    try:
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
    main()