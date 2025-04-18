"""
Run script for the Flask application with the GloriaMundo chatbot.
This is used to start the application on port 5000, accessible from anywhere.
"""
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)