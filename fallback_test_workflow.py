"""
Workflow for testing the model fallback confirmation feature.
This workflow runs a simple server that demonstrates the model fallback confirmation dialog.
"""
import logging
import model_fallback_test_standalone

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    """Run the fallback test server"""
    try:
        # Run the standalone test
        model_fallback_test_standalone.run()
    except Exception as e:
        logger.error(f"Error running fallback test: {e}")

if __name__ == "__main__":
    run()