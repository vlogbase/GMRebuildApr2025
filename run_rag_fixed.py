"""
Simple script to run the RAG-fixed Flask application for testing in the Replit environment.
"""

import logging
from app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("rag_fixed.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Flask application with fixed RAG functionality...")
    
    # Run the Flask app on host 0.0.0.0 to allow external access
    app.run(host='0.0.0.0', port=5000, debug=True)