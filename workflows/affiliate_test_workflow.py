"""
Test workflow for the simplified affiliate system
"""
import os
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run():
    """Run the Flask application with development settings enabled."""
    logger.info("Starting affiliate test workflow")
    
    # Environment setup
    os.environ["FLASK_APP"] = "app.py"
    os.environ["FLASK_ENV"] = "development"
    os.environ["FLASK_DEBUG"] = "1"
    
    # Import and run the Flask application
    logger.info("Importing Flask application")
    import app
    
    logger.info("Starting Flask server")
    
    # Run with host='0.0.0.0' to make the app accessible from outside
    app.app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

if __name__ == "__main__":
    run()