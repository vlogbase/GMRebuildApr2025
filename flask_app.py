"""
Simple script to run the Flask application for testing.
This is used by the Replit workflow to start the server.
"""
import os
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)