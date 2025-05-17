"""
Script to fix the fallback notification code in app.py
"""
import re
import os
import sys
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   filename='fix_fallback.log')
logger = logging.getLogger(__name__)

def backup_app_py():
    """Create a backup of app.py"""
    backup_filename = f'app.py.bak.fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    os.system(f'cp app.py {backup_filename}')
    logger.info(f"Created backup of app.py at {backup_filename}")
    return backup_filename

def fix_fallback_notification():
    """Fix the model fallback notification system in app.py"""
    try:
        # Create backup
        backup_file = backup_app_py()
        
        # Read current app.py
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Define the fallback notification section pattern
        # This regex captures the entire section that needs to be replaced
        pattern = r'(# Return a streaming response with a model_fallback event\s+def generate_fallback_notification\(\):.*?)(?=\s+return app\.response_class)'
        
        # Find the section that needs to be replaced
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            logger.error("Could not find the fallback notification section in app.py")
            return False
        
        old_code = match.group(1)
        logger.info(f"Found fallback notification section:\n{old_code}")
        
        # Define the fixed code
        new_code = """                    # Return a streaming response with a model_fallback event
                    def generate_fallback_notification():
                        try:
                            import json
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
                            # Return a simplified error fallback notification
                            try:
                                import json
                                error_json = json.dumps({
                                    'type': 'error', 
                                    'error': 'Failed to generate fallback notification'
                                })
                                yield f'data: {error_json}\\n\\n'
                            except Exception as e:
                                logger.error(f"Critical failure in fallback notification system: {e}")
                                yield f'data: {{\"type\":\"error\",\"error\":\"Internal server error\"}}\\n\\n'"""
        
        # Replace the old code with the fixed code
        updated_content = content.replace(old_code, new_code)
        
        # Write updated content back to app.py
        with open('app.py', 'w') as f:
            f.write(updated_content)
        
        logger.info("Fixed model fallback notification code in app.py")
        return True
    
    except Exception as e:
        logger.error(f"Error fixing model fallback notification: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    try:
        result = fix_fallback_notification()
        if result:
            print("Successfully fixed model fallback notification code in app.py")
        else:
            print("Failed to fix model fallback notification code in app.py")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)