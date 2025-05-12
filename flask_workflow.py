"""
Simple script to run the Flask application.
This serves as the entry point for the workflow.
"""
import os
import logging
from app import app

def run():
    """
    Run the Flask application with proper configuration.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='app_workflow.log'
    )
    
    # Print startup message
    print("Starting Flask application with unified file upload support...")
    print("Server will be available at http://0.0.0.0:5000")
    
    # Run the application
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

if __name__ == "__main__":
    run()