#!/usr/bin/env python3
"""
Simple script to run the Flask application for testing in the Replit environment.
"""
import os
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)