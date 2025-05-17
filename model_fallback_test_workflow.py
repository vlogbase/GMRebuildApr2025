"""
Workflow to test the model fallback confirmation feature
"""
import os
import logging
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    """Run the test script for model fallback confirmation"""
    try:
        # Import the test script
        import test_model_fallback
        
        # Run the test
        if test_model_fallback.run():
            print("=" * 80)
            print(" MODEL FALLBACK TEST SERVER RUNNING ")
            print("=" * 80)
            print("Navigate to: http://localhost:5000/test-fallback")
            print("=" * 80)
            
            # Return True to keep workflow running
            return True
        else:
            print("Failed to start model fallback test")
            return False
    except Exception as e:
        logger.error(f"Error running model fallback test: {e}")
        return False

if __name__ == "__main__":
    run()