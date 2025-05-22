"""
Simple Flask server workflow for GloriaMundo Chatbot
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application
    """
    try:
        # Import after logger configuration
        from app import app
        
        # Log the URL map to see all available routes
        logger.info("Available routes:")
        for rule in sorted(app.url_map.iter_rules(), key=lambda x: str(x)):
            logger.info(f"  {rule}")
        
        # Get port (default to 5000)
        port = int(os.environ.get("PORT", 5000))
        
        # Start the server
        logger.info(f"Starting Flask server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logger.error(f"Error starting server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run()