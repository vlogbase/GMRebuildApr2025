"""
Simple Flask server workflow for GloriaMundo Chat
This workflow runs the main Flask application for testing
"""

from app import app

def run():
    """
    Run the Flask application
    """
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()
