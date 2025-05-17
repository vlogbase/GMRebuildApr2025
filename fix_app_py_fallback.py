"""
Script to fix the syntax errors in app.py and ensure proper model fallback functionality.
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
                   filename='fix_fallback.log')
logger = logging.getLogger(__name__)

def fix_app_py():
    """Fix the syntax errors in app.py and improve model fallback functionality."""
    try:
        # Create a backup of the current app.py file
        backup_filename = f'app.py.bak.fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        os.system(f'cp app.py {backup_filename}')
        logger.info(f"Created backup: {backup_filename}")
        
        # Read the current content
        with open('app.py', 'r') as f:
            content = f.read()
        
        # 1. Fix the model fallback notification generation to ensure it includes proper error handling
        pattern1 = r'def generate_fallback_notification\(\):[^}]+yield f\'data: {fallback_json}\\n\\n\''
        replacement1 = '''def generate_fallback_notification():
                        try:
                            fallback_json = json.dumps({
                                'type': 'model_fallback',
                                'requested_model': original_model_name,
                                'fallback_model': fallback_model_name,
                                'original_model_id': openrouter_model,
                                'fallback_model_id': fallback_model
                            })
                            yield f'data: {fallback_json}\\n\\n'
                        except Exception as notification_error:
                            logger.error(f"Error generating fallback notification: {notification_error}")
                            logger.error(traceback.format_exc())
                            # Return a simplified error notification
                            error_json = json.dumps({
                                'type': 'model_fallback',
                                'requested_model': 'Unavailable Model',
                                'fallback_model': 'Basic Model',
                                'original_model_id': openrouter_model, 
                                'fallback_model_id': 'anthropic/claude-3-haiku-20240307'
                            })
                            yield f'data: {error_json}\\n\\n\''''
        content = re.sub(pattern1, replacement1, content)
        
        # 2. Fix error handling in the API preparation section
        pattern2 = r'# --- Prepare API Call ---\s+logger\.info\(.*\)\s+try:'
        replacement2 = '''# --- Prepare API Call ---
        logger.info(f"Preparing API call for model: {openrouter_model}")
        try:'''
        content = re.sub(pattern2, replacement2, content)
        
        # 3. Fix the exception handler for API preparation errors
        pattern3 = r'except Exception as api_prep_error:[^}]+abort\(500, description="Error in chat endpoint setup: API preparation failed"\)'
        replacement3 = '''        except Exception as api_prep_error:
            logger.error(f"Error in API call preparation: {api_prep_error}")
            logger.error(traceback.format_exc())
            abort(500, description="Error in chat endpoint setup: API preparation failed")'''
        content = re.sub(pattern3, replacement3, content)
        
        # 4. Make sure the model validation try block has proper error handling
        pattern4 = r'try:\s+import model_validator\s+logger\.info\("Starting model validation"\)'
        replacement4 = '''try:
            import model_validator
            logger.info("Starting model validation")
        except Exception as model_validator_error:
            logger.error(f"Error importing model validator: {model_validator_error}")
            logger.error(traceback.format_exc())
            abort(500, description="Error during model validation setup")'''
        content = re.sub(pattern4, replacement4, content)
        
        # 5. Fix typo in the model available check pattern
        pattern5 = r'logger\.info\(f"Checking if model {openrouter_model} is available"\)\s+model_available = model_validator\.is_model_available\(openrouter_model, available_models\)\s+logger\.info\(f"Model {openrouter_model} available: {model_available}"\)\s+\s+if not model_available or has_rag_content:\s+logger\.info\(f"Model unavailable or RAG content detected\. RAG content: {has_rag_content}"\)'
        replacement5 = '''            logger.info(f"Checking if model {openrouter_model} is available")
            model_available = model_validator.is_model_available(openrouter_model, available_models)
            logger.info(f"Model {openrouter_model} available: {model_available}")
            
            if not model_available or has_rag_content:
                logger.info(f"Model unavailable or RAG content detected. RAG content: {has_rag_content}")'''
        content = re.sub(pattern5, replacement5, content)
        
        # 6. Add a simple top-level exception handler for the chat endpoint
        pattern6 = r'@app\.route\(\'/chat\', methods=\[\'POST\'\]\)\s+def chat\(\):'
        replacement6 = '''@app.route('/chat', methods=['POST'])
def chat():
    try:'''
        content = re.sub(pattern6, replacement6, content)
        
        # 7. Add a catch-all exception handler at the end of the chat function
        pattern7 = r'# Clean up any conversation-specific resources\s+return response'
        replacement7 = '''        # Clean up any conversation-specific resources
        return response
    except Exception as chat_error:
        logger.error(f"Unhandled error in chat endpoint: {chat_error}")
        logger.error(traceback.format_exc())
        
        # Provide a friendly error response
        error_message = "We encountered an issue processing your request. Our team has been notified."
        if hasattr(chat_error, 'message'):
            error_message += f" Error details: {chat_error.message}"
        elif str(chat_error):
            error_message += f" Error details: {str(chat_error)}"
            
        # Use SSE format for error response to match expected client handling
        def generate_error_response():
            error_json = json.dumps({
                'type': 'error',
                'error': error_message
            })
            yield f'data: {error_json}\\n\\n'
            
        return app.response_class(
            generate_error_response(),
            mimetype='text/event-stream'
        )'''
        content = re.sub(pattern7, replacement7, content)
        
        # Write the fixed content back to app.py
        with open('app.py', 'w') as f:
            f.write(content)
        
        logger.info("Successfully fixed app.py and updated model fallback functionality")
        return True
    except Exception as e:
        logger.error(f"Error fixing app.py: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == '__main__':
    logger.info("Starting app.py fix")
    success = fix_app_py()
    if success:
        print("Successfully fixed app.py for model fallback functionality")
        print("Logs written to fix_fallback.log")
    else:
        print("Failed to fix app.py. See fix_fallback.log for details.")