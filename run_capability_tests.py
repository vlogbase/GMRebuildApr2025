#!/usr/bin/env python
"""
Model capability detection and multimodal content format adaptation tests.
This script verifies our fixes for the HTTP 400 errors.
"""
import os
import sys
import logging
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('capability_tests.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    # Check environment
    if not os.environ.get('OPENROUTER_API_KEY'):
        logger.error("OPENROUTER_API_KEY environment variable not set!")
        print("ERROR: Please set the OPENROUTER_API_KEY environment variable.")
        return 1
    
    print("\n--- Running Model Capability Detection Tests ---\n")
    
    # Run model capability tests
    try:
        import test_model_capabilities
        
        # The test will handle logging its own results
        test_model_capabilities.run_test()
        print("\nModel capability tests completed. See capability_tests.log for details.")
        print("Full report saved to model_capabilities_report.txt")
        
    except Exception as e:
        logger.error(f"Error running model capability tests: {e}")
        logger.error(traceback.format_exc())
        print(f"Error running tests: {e}")
        return 1
    
    print("\n--- Running OpenRouter API Integration Tests ---\n")
    
    # Run OpenRouter API tests if the capability tests succeeded
    try:
        import test_openrouter_api
        
        # The test will handle logging its own results
        test_openrouter_api.run_all_tests()
        print("\nOpenRouter API tests completed. See openrouter_test.log for details.")
        print("Full report saved to openrouter_test_report.txt")
        
    except Exception as e:
        logger.error(f"Error running OpenRouter API tests: {e}")
        logger.error(traceback.format_exc())
        print(f"Error running tests: {e}")
        return 1
    
    print("\n--- All Tests Completed Successfully ---\n")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTests stopped by user.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error in main: {e}")
        logger.critical(traceback.format_exc())
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)