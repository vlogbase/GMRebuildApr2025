"""
Test workflow for the model fallback confirmation feature

This workflow runs the Flask application with logging focused on 
the model selection and fallback handling.
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# Add the parent directory to the Python path
# This allows us to import app correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import app after path is set
from app import app

def setup_logging():
    """Configure detailed logging for testing the model fallback feature"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure file handler with rotation
    file_handler = RotatingFileHandler(
        'logs/model_fallback_test.log',
        maxBytes=1024 * 1024 * 10,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Get the root logger and configure it
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Add specific loggers for components we're testing
    for logger_name in ['app.chat', 'app.model_validator', 'app.user_settings']:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

def run():
    """Run the Flask application with debugging enabled"""
    # Set up detailed logging
    setup_logging()
    
    # Log the start of the test workflow
    logging.info("Starting model fallback confirmation test workflow")
    
    # Set the host to make the app accessible
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app with debugging enabled
    app.run(host=host, port=port, debug=True, use_reloader=True)

if __name__ == '__main__':
    run()