#!/usr/bin/env python3
"""
Simple Flask server runner for testing the application.
This ensures the database is initialized before running the app.
"""
import os
from app import app, db

# Make sure all tables exist
with app.app_context():
    db.create_all()

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)