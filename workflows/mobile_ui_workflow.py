"""
Mobile UI testing workflow for GloriaMundo Chatbot

This workflow runs a simplified version of the app to test mobile interface changes.
"""

import os
import sys
import time
import logging

# Add the parent directory to sys.path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template

# Create a simple Flask app for testing the mobile UI
app = Flask(__name__, template_folder="../templates", static_folder="../static")

@app.route('/')
def index():
    """Render the index page to test mobile UI components"""
    return render_template('index.html')

def run():
    """Run the Flask application for mobile UI testing"""
    print("Starting Mobile UI Test Workflow...")
    print("Use the webview to test the mobile interface changes")
    print("Server running on http://0.0.0.0:5000")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()