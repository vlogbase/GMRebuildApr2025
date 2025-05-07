"""
Testing workflow for the OpenRouter integration

This script runs various tests to verify our OpenRouter API integration is working correctly.
"""
import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("openrouter_tests.log")
    ]
)
logger = logging.getLogger(__name__)

def run_openrouter_api_tests():
    """Run tests for the OpenRouter API integration."""
    logger.info("Running OpenRouter API Tests...")
    
    try:
        # Import the test module
        sys.path.append('.')
        import test_openrouter_api
        
        # Run the tests
        test_openrouter_api.run_all_tests()
        
        logger.info("OpenRouter API Tests completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error running OpenRouter API tests: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def run_model_validation_tests():
    """Run tests for the model validation module."""
    logger.info("Running Model Validation Tests...")
    
    try:
        # Import the validation module
        sys.path.append('.')
        import model_validator
        
        # Test getting available models
        available_models = model_validator.get_available_models()
        logger.info(f"Found {len(available_models)} available models")
        
        # Test model availability check
        test_model = "anthropic/claude-3-haiku-20240307"
        is_available = model_validator.is_model_available(test_model, available_models)
        logger.info(f"Model {test_model} availability: {is_available}")
        
        # Test fallback mechanism
        non_existent_model = "nonexistent/model-id"
        fallback_models = [
            "anthropic/claude-3-haiku-20240307",
            "google/gemini-pro-vision",
            "meta-llama/llama-3-8b",
            "mistralai/mistral-7b"
        ]
        
        fallback = model_validator.get_fallback_model(
            non_existent_model, 
            fallback_models,
            available_models
        )
        logger.info(f"Fallback for {non_existent_model}: {fallback}")
        
        # Test multimodal fallback selection
        multimodal_model = model_validator.select_multimodal_fallback(True, available_models)
        logger.info(f"Selected multimodal model: {multimodal_model}")
        
        text_model = model_validator.select_multimodal_fallback(False, available_models)
        logger.info(f"Selected text model: {text_model}")
        
        logger.info("Model Validation Tests completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error running model validation tests: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def run_model_verification():
    """Run the model verification script."""
    logger.info("Running Model Verification...")
    
    try:
        # Import the verification module
        sys.path.append('.')
        import run_model_verification
        
        # Run verification
        run_model_verification.run_verification()
        
        logger.info("Model Verification completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error running model verification: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def run():
    """Main function to run all tests."""
    logger.info("Starting OpenRouter Integration Tests...")
    print("Starting OpenRouter Integration Tests...")
    
    # Run all test suites
    api_tests_ok = run_openrouter_api_tests()
    validation_tests_ok = run_model_validation_tests()
    verification_ok = run_model_verification()
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"TEST SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"API Tests: {'✅ PASSED' if api_tests_ok else '❌ FAILED'}")
    print(f"Validation Tests: {'✅ PASSED' if validation_tests_ok else '❌ FAILED'}")
    print(f"Model Verification: {'✅ PASSED' if verification_ok else '❌ FAILED'}")
    print("=" * 60)
    
    if api_tests_ok and validation_tests_ok and verification_ok:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED - Check logs for details")
    
    logger.info("OpenRouter Integration Tests completed.")

if __name__ == "__main__":
    run()