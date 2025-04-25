"""
Flask application workflow runner
"""
import os
import sys
from app import app

def run():
    """
    Run the Flask application with the development server
    """
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()