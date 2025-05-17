"""
Simple workflow for testing the model fallback confirmation feature
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
        return True
    except Exception as e:
        logger.error(f"Error running fallback test: {e}")
        return False

if __name__ == "__main__":
    run()