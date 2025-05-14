"""
Test workflow for the send button functionality
"""

import os
from app import app

def run():
    """
    Run the Flask application to test the send button functionality
    """
    # Set the port and host
    port = int(os.environ.get("PORT", 5000))
    
    # Run the app
    app.run(host="0.0.0.0", port=port, debug=True)

if __name__ == "__main__":
    run()