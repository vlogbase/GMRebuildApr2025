"""
Test workflow for the simplified affiliate system
"""
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application for testing the affiliate system
    """
    # Import Flask app
    from app import app
    from flask_login import current_user
    
    # Override PORT environment variable
    os.environ['PORT'] = '5000'
    
    # Configure Flask development settings
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['DEBUG'] = True
    
    logger.info("Starting affiliate test workflow")
    logger.info(f"Server will run at http://0.0.0.0:5000")
    
    # Start the server
    app.run(host='0.0.0.0', port=5000, debug=True)
    
if __name__ == '__main__':
    run()