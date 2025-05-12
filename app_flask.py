"""
Simple server runner for our Flask application
This is the file we'll run to start our application
"""

from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)