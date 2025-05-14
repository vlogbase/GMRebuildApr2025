"""
Test workflow for the memory preference toggle
"""
import os
import sys
import logging
from app import app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='memory_test_workflow.log'
)

def run():
    """
    Run the Flask application with memory system enabled
    """
    # Ensure memory system is enabled for testing
    os.environ['ENABLE_MEMORY_SYSTEM'] = 'true'
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logging.error(f"Error starting the app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()