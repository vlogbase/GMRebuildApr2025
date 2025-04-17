"""
Script to start the Flask application for the Replit workflow.
"""
import os
import logging
from gevent import monkey
monkey.patch_all()  # Patch all for gevent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import Flask app after gevent patching
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
