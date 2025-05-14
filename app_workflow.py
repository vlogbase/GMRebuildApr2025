"""
Simple Flask server workflow for testing the application
"""
import os
from app import app

def run():
    """
    Run the Flask application
    """
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()
