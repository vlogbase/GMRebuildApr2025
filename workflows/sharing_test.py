"""
Workflow to test the improved conversation sharing functionality
"""
import sys
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

def run():
    """Run the Flask application to test conversation sharing"""
    try:
        logger.info("Starting Flask app to test conversation sharing improvements...")
        
        from app import app
        
        host = '0.0.0.0'
        port = int(os.environ.get('PORT', 5000))
        
        app.run(host=host, port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    run()