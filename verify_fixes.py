"""
Simple script to verify our PDF support fixes
"""
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('verify.log')
    ]
)

logger = logging.getLogger(__name__)

def verify_app_context():
    """Verify that app context functions are working"""
    try:
        # Import our context manager
        from ensure_app_context import ensure_app_context
        logger.info("✅ Successfully imported ensure_app_context module")
        
        # Test the context manager
        with ensure_app_context():
            logger.info("✅ Successfully created app context")
            
        logger.info("App context verification completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error verifying app context: {e}")
        return False

def verify_message_model():
    """Verify that Message model has PDF fields"""
    try:
        # Import Message model
        from models import Message
        logger.info("✅ Successfully imported Message model")
        
        # Check if PDF fields exist
        model_instance = Message()
        if hasattr(model_instance, 'pdf_url'):
            logger.info("✅ Message model has pdf_url field")
        else:
            logger.error("❌ Message model is missing pdf_url field")
            return False
            
        if hasattr(model_instance, 'pdf_filename'):
            logger.info("✅ Message model has pdf_filename field")
        else:
            logger.error("❌ Message model is missing pdf_filename field")
            return False
            
        logger.info("Message model verification completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error verifying Message model: {e}")
        return False

def run_verification():
    """Run all verification checks"""
    logger.info("=== Starting verification of PDF support fixes ===")
    
    app_context_ok = verify_app_context()
    message_model_ok = verify_message_model()
    
    # Print summary
    logger.info("=== Verification Results ===")
    logger.info(f"App Context: {'✅ OK' if app_context_ok else '❌ Failed'}")
    logger.info(f"Message Model: {'✅ OK' if message_model_ok else '❌ Failed'}")
    
    # Overall result
    if app_context_ok and message_model_ok:
        logger.info("🎉 All PDF support fixes verified successfully!")
        return True
    else:
        logger.error("⚠️ Some verification checks failed.")
        return False

if __name__ == "__main__":
    run_verification()