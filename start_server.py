"""
Script to start the Flask application with the right settings.

This file is used by the Replit workflow system to start the server.
"""
import os
import sys
from app import app

if __name__ == "__main__":
    # Set host to 0.0.0.0 to make the server publicly accessible
    # Set port to 5000 or use the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)