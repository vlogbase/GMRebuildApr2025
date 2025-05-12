"""
Script to check that our fixes were applied correctly.
"""
import os
import sys
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_price_updater_fix():
    """
    Check that price_updater.py has the app context fixes.
    """
    try:
        with open('price_updater.py', 'r') as f:
            content = f.read()
        
        # Check for app context in import
        has_app_import = 'from app import app, db' in content
        
        # Check for app context in fetch_and_store_openrouter_prices
        has_app_context = 'with app.app_context()' in content
        
        if has_app_import and has_app_context:
            logger.info("✅ price_updater.py has app context fixes")
            return True
        else:
            if not has_app_import:
                logger.error("❌ price_updater.py is missing app import")
            if not has_app_context:
                logger.error("❌ price_updater.py is missing app context")
            return False
    except Exception as e:
        logger.error(f"Error checking price_updater.py: {e}")
        return False

def check_get_models_api_fix():
    """
    Check that app.py includes supports_pdf in the get_models API.
    """
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Define pattern for model_data in get_models
        pattern = r"model_data\s*=\s*{.*?'supports_pdf':\s*db_model\.supports_pdf.*?}"
        
        # Check for supports_pdf in model_data
        has_supports_pdf = re.search(pattern, content, re.DOTALL) is not None
        
        if has_supports_pdf:
            logger.info("✅ get_models API includes supports_pdf flag")
            return True
        else:
            logger.error("❌ get_models API is missing supports_pdf flag")
            return False
    except Exception as e:
        logger.error(f"Error checking app.py: {e}")
        return False

if __name__ == "__main__":
    logger.info("Checking fixes for price_updater.py and get_models API...")
    
    price_updater_fix = check_price_updater_fix()
    get_models_api_fix = check_get_models_api_fix()
    
    if price_updater_fix and get_models_api_fix:
        logger.info("✅ All fixes applied successfully!")
        sys.exit(0)
    else:
        if not price_updater_fix:
            logger.error("❌ price_updater.py fixes not applied")
        if not get_models_api_fix:
            logger.error("❌ get_models API fixes not applied")
        sys.exit(1)