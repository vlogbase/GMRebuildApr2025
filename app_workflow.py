"""
Simple script to run the Flask application for testing in the Replit environment.
This is a wrapper script to start the app.py Flask application.
"""

def run():
    """
    Run the Flask application with error handling and logging.
    """
    import logging
    from app import app
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Flask application...")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error running Flask application: {e}")
        logger.exception("Detailed error:")

if __name__ == "__main__":
    run()
