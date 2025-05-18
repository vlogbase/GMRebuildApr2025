"""
Test workflow for the marketing page
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def run():
    """Run the Flask application for testing the marketing page"""
    logger.info("Starting Flask server for marketing page test")
    
    # Set Flask environment variables
    os.environ["FLASK_APP"] = "app.py"
    os.environ["FLASK_ENV"] = "development"
    os.environ["FLASK_DEBUG"] = "1"
    
    # Import the Flask app
    import app
    
    # Run the application
    app.app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    run()