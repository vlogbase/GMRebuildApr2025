"""
Run the Flask application with the proper app context configuration
"""
import os
import logging
from ensure_app_context import ensure_app_context

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app_new.log')
    ]
)

logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application with app context handling
    """
    try:
        # Import Flask app
        from app import app
        
        logger.info("Starting Flask application with app context handling")
        
        # Use our context manager to ensure app context is available
        with ensure_app_context():
            # Run the Flask app
            app.run(
                host="0.0.0.0",
                port=int(os.environ.get("PORT", 5000)),
                debug=True, 
                use_reloader=False
            )
    except Exception as e:
        logger.exception(f"Error running Flask application: {e}")

if __name__ == "__main__":
    run()