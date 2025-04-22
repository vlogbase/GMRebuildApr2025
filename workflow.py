#!/usr/bin/env python3
"""
Flask application workflow for running in Replit.
This is a simple script that runs the Flask app.
"""
import os
from app import app

# Run the Flask app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)