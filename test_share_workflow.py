"""
Test workflow to debug the shared conversation functionality.
"""
import os
import logging
from app import app

def run():
    """
    Run the Flask application in debug mode.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Print startup message
    print("Starting Flask application for share functionality testing...")
    print("Server will be available at http://0.0.0.0:5000")
    
    # Run the application with debug mode enabled
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

if __name__ == "__main__":
    run()