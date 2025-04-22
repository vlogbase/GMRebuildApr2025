"""
Simple script to run the Flask application for testing in the Replit environment.
"""
import os
from app import app

# Get the port from the environment or use 5000 as a default
port = int(os.environ.get("PORT", 5000))

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=True)