"""
Script to fix the syntax errors introduced by the error logging enhancements.
"""
import os
import sys
import re
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   filename='fix_logging.log')
logger = logging.getLogger(__name__)

def fix_app_py():
    """Fix the syntax errors in app.py caused by the error logging script."""
    try:
        # Create a backup of the current app.py file
        backup_filename = f'app.py.bak.fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        os.system(f'cp app.py {backup_filename}')
        logger.info(f"Created backup: {backup_filename}")
        
        # Read the current content
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Fix missing except or finally clauses
        pattern1 = r'try:\s+import model_validator\s+logger\.info\("Starting model validation"\)'
        replacement1 = '''try:
            import model_validator
            logger.info("Starting model validation")
        except Exception as model_validator_error:
            logger.error(f"Error importing model validator: {model_validator_error}")
            logger.error(traceback.format_exc())
            abort(500, description="Error during model validation setup")'''
        content = re.sub(pattern1, replacement1, content)
        
        # Fix the second try block
        pattern2 = r'# --- Prepare API Call ---\s+logger\.info\(f"Preparing API call for model: {openrouter_model}"\)\s+try:'
        replacement2 = '''# --- Prepare API Call ---
        logger.info(f"Preparing API call for model: {openrouter_model}")
        try:'''
        content = re.sub(pattern2, replacement2, content)
        
        # Fix unexpected indentation in api_prep_error
        pattern3 = r'except Exception as api_prep_error:\s+logger\.error\(.*\)\s+logger\.error\(traceback\.format_exc\(\)\)\s+abort\(500, description="Error in chat endpoint setup: API preparation failed"\)'
        replacement3 = '''        except Exception as api_prep_error:
            logger.error(f"Error in API call preparation: {api_prep_error}")
            logger.error(traceback.format_exc())
            abort(500, description="Error in chat endpoint setup: API preparation failed")'''
        content = re.sub(pattern3, replacement3, content)
        
        # Fix the model availability check replacement
        pattern4 = r'logger\.info\(f"Checking if model {openrouter_model} is available"\)\s+model_available = model_validator\.is_model_available\(openrouter_model, available_models\)\s+logger\.info\(f"Model {openrouter_model} available: {model_available}"\)\s+\s+if not model_available or has_rag_content:\s+logger\.info\(f"Model unavailable or RAG content detected\. RAG content: {has_rag_content}"\)'
        replacement4 = '''            logger.info(f"Checking if model {openrouter_model} is available")
            model_available = model_validator.is_model_available(openrouter_model, available_models)
            logger.info(f"Model {openrouter_model} available: {model_available}")
            
            if not model_available or has_rag_content:
                logger.info(f"Model unavailable or RAG content detected. RAG content: {has_rag_content}")'''
        content = re.sub(pattern4, replacement4, content)
        
        # Fix missing OPENROUTER_MODELS_INFO variable
        if 'OPENROUTER_MODELS_INFO' not in content:
            # Add it after OPENROUTER_MODELS declaration
            pattern5 = r'OPENROUTER_MODELS = {'
            replacement5 = '''OPENROUTER_MODELS = {'''
            content = re.sub(pattern5, replacement5, content)
            
            # Add the OPENROUTER_MODELS_INFO variable initialization after the OPENROUTER_MODELS dictionary
            pattern6 = r'}\s+# Define the default preset models'
            replacement6 = '''}

# Initialize OpenRouter models info - will be populated later
OPENROUTER_MODELS_INFO = []

# Define the default preset models'''
            content = re.sub(pattern6, replacement6, content)
        
        # Write the fixed content back to app.py
        with open('app.py', 'w') as f:
            f.write(content)
        
        logger.info("Successfully fixed app.py syntax errors")
        return True
    except Exception as e:
        logger.error(f"Error fixing app.py: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == '__main__':
    success = fix_app_py()
    if success:
        print("Successfully fixed syntax errors in app.py")
    else:
        print("Failed to fix syntax errors. See fix_logging.log for details.")