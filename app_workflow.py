"""
Test workflow script for GloriaMundo Chatbot

This script runs the Flask application to test the new model fallback preference feature.
"""
import os
from app import app

def run():
    """Run the Flask application."""
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

if __name__ == "__main__":
    run()