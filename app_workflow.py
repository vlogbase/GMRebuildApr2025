"""
Simple Flask server workflow for the main application with optimized cleanup
"""
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app_workflow.log'
)

logger = logging.getLogger(__name__)

def run():
    """
    Run the Flask application for testing
    """
    try:
        logger.info("Starting Flask app with optimized conversation cleanup")
        from app import app
        
        # Run the app
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except Exception as e:
        logger.exception(f"Error running app: {e}")

if __name__ == "__main__":
    run()