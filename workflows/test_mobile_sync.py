"""
Test workflow for mobile synchronization fixes
"""
import os
import sys
from flask import Flask, render_template

# Add the current directory to the path so we can import app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import app directly
import app

def run():
    """
    Run the Flask application with minimal components needed to test mobile synchronization
    """
    # Run the Flask app directly 
    app.app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    run()