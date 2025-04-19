"""
Simple script to run the Flask application.
"""
import os
from app import app

if __name__ == "__main__":
    # Get the port from environment variables, default to 5000
    port = int(os.environ.get("PORT", 5000))
    # Run the app
    app.run(host="0.0.0.0", port=port, debug=True)