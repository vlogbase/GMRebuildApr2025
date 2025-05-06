"""
Check PayPal Environment and SDK Availability

This script checks if the PayPal SDK is properly installed and configured.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_paypal_environment():
    """Check if PayPal environment variables are set"""
    
    required_vars = ['PAYPAL_CLIENT_ID', 'PAYPAL_CLIENT_SECRET']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required PayPal environment variables: {', '.join(missing_vars)}")
        logger.info("Please set these variables in your .env file or environment")
        return False
    
    mode = os.environ.get('PAYPAL_MODE', 'sandbox')
    logger.info(f"PayPal mode is set to: {mode}")
    
    return True

def check_paypal_sdk():
    """Check if PayPal SDK is installed and can be imported"""
    
    try:
        import paypalrestsdk
        logger.info("PayPal REST SDK imported successfully")
        
        # Try initializing the SDK
        from paypal_config import initialize_paypal
        
        result = initialize_paypal()
        if result:
            logger.info("PayPal SDK initialized successfully")
        else:
            logger.error("Failed to initialize PayPal SDK")
        
        return result
        
    except ImportError as e:
        logger.error(f"Failed to import PayPal SDK: {e}")
        logger.info("Please make sure paypalrestsdk is installed via pip")
        return False
    except Exception as e:
        logger.error(f"Error checking PayPal SDK: {e}")
        return False

def main():
    """Main function"""
    print("Checking PayPal environment and SDK availability...")
    
    env_check = check_paypal_environment()
    sdk_check = check_paypal_sdk()
    
    if env_check and sdk_check:
        print("\n✅ PayPal is properly configured and ready to use")
        return 0
    else:
        print("\n❌ PayPal configuration check failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())