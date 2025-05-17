"""
Script to enhance error handling in the chat endpoint.

This script adds structured error handling to catch and properly
report specific issues when processing chat messages, especially
when dealing with model fallback scenarios.
"""
import os
import sys
import re
import logging
import traceback
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='chat_error_handling.log'
)
logger = logging.getLogger(__name__)

def backup_app_py():
    """Create a backup of app.py"""
    backup_filename = f'app.py.bak.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        with open(backup_filename, 'w') as f:
            f.write(content)
        logger.info(f"Created backup: {backup_filename}")
        return content
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return None

def enhance_error_handling():
    """Add enhanced error handling to the chat endpoint"""
    # Create backup and read current content
    content = backup_app_py()
    if not content:
        return False
    
    try:
        # 1. Add structured error handling around fallback detection
        fallback_pattern = r'# Check if the requested model is available\s+if not model_validator\.is_model_available\(openrouter_model, available_models\) or has_rag_content:'
        fallback_replacement = '''# Check if the requested model is available
            try:
                model_available = model_validator.is_model_available(openrouter_model, available_models)
                if not model_available or has_rag_content:'''
        content = re.sub(fallback_pattern, fallback_replacement, content)
        
        # 2. Add catch block for the fallback check
        fallback_end_pattern = r'logger\.info\(f"Using adaptive model selection: {adaptive_model} \(image content: {has_image}, RAG content: {has_rag_content}\)"\)\s+openrouter_model = adaptive_model'
        fallback_end_replacement = '''logger.info(f"Using adaptive model selection: {adaptive_model} (image content: {has_image}, RAG content: {has_rag_content})")
                        openrouter_model = adaptive_model
            except Exception as fallback_error:
                logger.error(f"Error during model fallback selection: {fallback_error}")
                logger.error(traceback.format_exc())
                # If fallback fails, use a guaranteed safe model
                openrouter_model = "openai/gpt-3.5-turbo"
                logger.info(f"Using guaranteed fallback model: {openrouter_model} after error")'''
        content = re.sub(fallback_end_pattern, fallback_end_replacement, content)
        
        # 3. Improve error handling for the model fallback notification
        notification_pattern = r'def generate_fallback_notification\(\):\s+fallback_json = json\.dumps\({'
        notification_replacement = '''def generate_fallback_notification():
                        try:
                            fallback_json = json.dumps({'''
        content = re.sub(notification_pattern, notification_replacement, content)
        
        # 4. Add catch block for the fallback notification
        notification_end_pattern = r'yield f\'data: {fallback_json}\\n\\n\''
        notification_end_replacement = '''yield f'data: {fallback_json}\\n\\n'
                        except Exception as notification_error:
                            logger.error(f"Error generating fallback notification: {notification_error}")
                            logger.error(traceback.format_exc())
                            # Return a simplified error fallback notification
                            error_json = json.dumps({
                                'type': 'model_fallback',
                                'requested_model': 'Unavailable Model',
                                'fallback_model': 'Basic Fallback',
                                'original_model_id': openrouter_model,
                                'fallback_model_id': 'openai/gpt-3.5-turbo'
                            })
                            yield f'data: {error_json}\\n\\n\''''
        content = re.sub(notification_end_pattern, notification_end_replacement, content)
        
        # 5. Add top-level try-except around the entire chat endpoint
        chat_endpoint_pattern = r'@app\.route\(\'/chat\', methods=\[\'POST\'\]\)\s+def chat\(\): # Synchronous function'
        chat_endpoint_replacement = '''@app.route('/chat', methods=['POST'])
def chat(): # Synchronous function
    """
    Endpoint to handle chat messages and stream responses from OpenRouter (SYNC Version)
    """
    try:'''
        content = re.sub(chat_endpoint_pattern, chat_endpoint_replacement, content)
        
        # 6. Add final catch-all exception handler at the end of the chat function
        chat_end_pattern = r'# Clean up any conversation-specific resources\s+return response'
        chat_end_replacement = '''# Clean up any conversation-specific resources
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
        content = re.sub(chat_end_pattern, chat_end_replacement, content)
        
        # 7. Wrap API call in better error handling for better error transparency
        api_call_pattern = r'# Make API call to OpenRouter\s+response = requests\.post\('
        api_call_replacement = '''# Make API call to OpenRouter
                try:
                    response = requests.post('''
        content = re.sub(api_call_pattern, api_call_replacement, content)
        
        # 8. Add catch block for API call
        api_call_end_pattern = r'if response\.status_code != 200:'
        api_call_end_replacement = '''                except Exception as api_error:
                    logger.error(f"Error making API call to OpenRouter: {api_error}")
                    logger.error(traceback.format_exc())
                    # Generate error response for client
                    yield f'data: {{"type": "error", "error": "Connection error while reaching OpenRouter API."}}\\n\\n'
                    return
                    
                if response.status_code != 200:'''
        content = re.sub(api_call_end_pattern, api_call_end_replacement, content)
        
        # Write the updated content back to app.py
        with open('app.py', 'w') as f:
            f.write(content)
        
        logger.info("Successfully enhanced error handling in app.py")
        return True
    except Exception as e:
        logger.error(f"Error enhancing error handling: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == '__main__':
    logger.info("Starting error handling enhancement")
    success = enhance_error_handling()
    if success:
        print("Successfully enhanced error handling in app.py")
        print("Error logs will be written to chat_error_handling.log")
    else:
        print("Failed to enhance error handling. Check chat_error_handling.log for details.")