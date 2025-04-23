#!/usr/bin/env python3
"""
Simple server runner for our Flask application
"""
import os
from app import app

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)