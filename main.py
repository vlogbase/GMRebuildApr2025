"""
Main entry point for the GloriaMundo Chatbot application.
This file imports the app instance from app.py and serves as the entry point for WSGI servers.
"""
from app import app  # noqa: F401

# This file is used by WSGI servers (gunicorn) to find the app instance.
# The actual application logic is in app.py.

if __name__ == "__main__":
    # Run the Flask development server when executed directly
    app.run(host="0.0.0.0", port=5000, debug=True)