"""
Simple script to run the Flask application with the admin panel.
"""

from app import app

def run():
    """
    Run the Flask application.
    
    Note: The admin panel is already initialized in app.py
    so we don't need to do that here.
    """
    print("Starting Flask application...")
    app.run(debug=True, port=5000, host='0.0.0.0')

if __name__ == '__main__':
    run()