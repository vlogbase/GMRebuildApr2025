"""
Enhanced logging module for diagnosing chat endpoint errors.

This script adds detailed logging around the critical sections of the
chat endpoint in app.py, specifically focusing on model validation
and fallback handling to diagnose 500 errors.
"""
import sys
import os
import re
import logging
import traceback
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='chat_debug.log'
)
logger = logging.getLogger(__name__)

def apply_error_logging():
    """Apply enhanced error logging to the Flask app's chat endpoint."""
    try:
        # Read the app.py file
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        # Create a backup of the original file
        backup_filename = f'app.py.bak.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        with open(backup_filename, 'w') as f:
            f.write(app_content)
        logger.info(f"Created backup of app.py at {backup_filename}")
        
        # Add imports if needed
        if 'import traceback' not in app_content:
            app_content = re.sub(
                r'import logging',
                'import logging\nimport traceback',
                app_content
            )
        
        # Add detailed logging to the model validation section
        model_validation_pattern = r'try:\s+import model_validator\s+'
        model_validation_replacement = '''try:
            import model_validator
            logger.info("Starting model validation")
            '''
        app_content = re.sub(model_validation_pattern, model_validation_replacement, app_content)
        
        # Add detailed logging to the get_available_models function call
        available_models_pattern = r'available_models = model_validator\.get_available_models\(\)'
        available_models_replacement = '''logger.info("Fetching available models")
            try:
                available_models = model_validator.get_available_models()
                logger.info(f"Retrieved {len(available_models)} available models")
            except Exception as e:
                logger.error(f"Error getting available models: {e}")
                logger.error(traceback.format_exc())
                available_models = []'''
        app_content = re.sub(available_models_pattern, available_models_replacement, app_content)
        
        # Add detailed logging to the model availability check
        model_check_pattern = r'if not model_validator\.is_model_available\(openrouter_model, available_models\) or has_rag_content:'
        model_check_replacement = '''logger.info(f"Checking if model {openrouter_model} is available")
            model_available = model_validator.is_model_available(openrouter_model, available_models)
            logger.info(f"Model {openrouter_model} available: {model_available}")
            
            if not model_available or has_rag_content:
                logger.info(f"Model unavailable or RAG content detected. RAG content: {has_rag_content}")'''
        app_content = re.sub(model_check_pattern, model_check_replacement, app_content)
        
        # Add detailed logging to the fallback model selection
        fallback_model_pattern = r'fallback_model = model_validator\.get_fallback_model\('
        fallback_model_replacement = '''logger.info("Attempting to find fallback model")
                try:
                    fallback_model = model_validator.get_fallback_model('''
        app_content = re.sub(fallback_model_pattern, fallback_model_replacement, app_content)
        
        # Add detailed logging after fallback model selection
        fallback_selection_pattern = r'openrouter_model = fallback_model'
        fallback_selection_replacement = '''logger.info(f"Selected fallback model: {fallback_model}")
                    openrouter_model = fallback_model'''
        app_content = re.sub(fallback_selection_pattern, fallback_selection_replacement, app_content)
        
        # Add detailed error handling for API call preparation
        api_prep_pattern = r'# --- Prepare API Call ---'
        api_prep_replacement = '''# --- Prepare API Call ---
        logger.info(f"Preparing API call for model: {openrouter_model}")
        try:'''
        app_content = re.sub(api_prep_pattern, api_prep_replacement, app_content)
        
        # Add catch block at the end of API preparation
        response_pattern = r'return app\.response_class\('
        response_replacement = '''except Exception as api_prep_error:
            logger.error(f"Error in API call preparation: {api_prep_error}")
            logger.error(traceback.format_exc())
            abort(500, description="Error in chat endpoint setup: API preparation failed")
        
        return app.response_class('''
        app_content = re.sub(response_pattern, response_replacement, app_content)
        
        # Add detailed error logging to the OpenRouter API call
        openrouter_call_pattern = r'try:\s+# Make API call to OpenRouter'
        openrouter_call_replacement = '''try:
            # Log the API request details
            logger.info(f"Making OpenRouter API call for model: {openrouter_model}")
            logger.info(f"API request payload keys: {list(payload.keys()) if payload else []}")
            
            # Make API call to OpenRouter'''
        app_content = re.sub(openrouter_call_pattern, openrouter_call_replacement, app_content)
        
        # Write the modified content back to app.py
        with open('app.py', 'w') as f:
            f.write(app_content)
        
        logger.info("Successfully applied error logging enhancements to app.py")
        return True
    except Exception as e:
        logger.error(f"Failed to apply error logging: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == '__main__':
    logger.info("Starting enhanced error logging application")
    result = apply_error_logging()
    if result:
        print("Successfully applied enhanced error logging to app.py")
        print("Debug logs will be written to chat_debug.log")
    else:
        print("Failed to apply enhanced error logging. See chat_debug.log for details.")