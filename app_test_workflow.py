"""
Test workflow for the Flask application
"""
import os
import sys
from app import app

def run():
    """
    Run the Flask application for testing
    """
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))
    app.run(host=HOST, port=PORT, debug=True)

if __name__ == "__main__":
    run()