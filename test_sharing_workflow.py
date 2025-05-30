"""
Test workflow for the improved conversation sharing functionality
"""
import sys
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to import app
sys.path.append(str(Path(__file__).parent))

def run():
    """
    Run the Flask application to test the improved sharing functionality
    """
    try:
        logger.info("Starting Flask application to test conversation sharing improvements...")
        
        # Import the Flask app
        from app import app
        
        # Run the Flask app on host 0.0.0.0 to allow external access
        host = '0.0.0.0'
        port = int(os.environ.get('PORT', 5000))
        
        logger.info(f"Starting Flask app on {host}:{port}")
        logger.info("Testing features:")
        logger.info("1. Owner viewing shared link -> redirects to interactive chat")
        logger.info("2. Different user viewing shared link -> forks conversation")
        logger.info("3. Guest viewing shared link -> shows beautiful public interface")
        
        # Run the application
        app.run(host=host, port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Error running Flask application: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    run()