"""
Simple script to run the Flask application directly.
This can be used to test the application without using Gunicorn.
"""
from app import app

if __name__ == "__main__":
    # Run the Flask application in debug mode
    app.run(host="0.0.0.0", port=5000, debug=True)