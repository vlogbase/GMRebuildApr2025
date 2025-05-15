"""
Simple workflow to test the mobile UI improvements
"""

from app import app

def run():
    """
    Run the Flask application to test the mobile UI
    """
    app.run(host='0.0.0.0', port=5000, debug=True)