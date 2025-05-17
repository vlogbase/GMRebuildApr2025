"""
Test script for the model fallback confirmation feature.

This script runs the Flask application with a specific model marked as unavailable
to test the model fallback confirmation dialog and user preference handling.
"""
import os
import logging
from app import app

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('model_fallback_test.log'),
        logging.StreamHandler()
    ]
)

# Set up a logger for this test
logger = logging.getLogger('model_fallback_test')
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    # Mark a specific model as unavailable to trigger the fallback confirmation
    # This common model will be used for testing the fallback mechanism
    os.environ['TEST_UNAVAILABLE_MODEL'] = 'anthropic/claude-3-haiku-20240307'
    
    # Log test configuration
    logger.info("=" * 70)
    logger.info("Starting Model Fallback Confirmation Feature Test")
    logger.info(f"Test unavailable model: {os.environ['TEST_UNAVAILABLE_MODEL']}")
    logger.info("=" * 70)
    
    # Print instructions for testing
    print("\nTEST INSTRUCTIONS:")
    print("1. Select the model that's marked as unavailable (claude-3-haiku)")
    print("2. Send a message to test the fallback confirmation dialog")
    print("3. Try both accepting and rejecting the fallback model")
    print("4. Test the 'Always use fallback models automatically' checkbox")
    print("5. Verify the preference is saved in the account settings page\n")
    
    # Run the app with debugging enabled
    app.run(host='0.0.0.0', port=5000, debug=True)