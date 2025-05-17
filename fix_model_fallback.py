"""
Script to fix all model fallback handling code in app.py
This script focuses on creating clean, consistent indentation in key sections.
"""
import re
import os
import sys
import shutil
from datetime import datetime

# Create a backup first
backup_file = f"app.py.bak.fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy2('app.py', backup_file)
print(f"Created backup: {backup_file}")

# Safe wrapper for modifying app.py
def safe_modify_app_py(modify_func):
    try:
        # Read the current content
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Apply the modifications
        modified_content = modify_func(content)
        
        # Write back the modified content
        with open('app.py', 'w') as f:
            f.write(modified_content)
        
        return True
    except Exception as e:
        print(f"Error modifying app.py: {e}")
        return False

# Function to fix the user chat settings auto_fallback_enabled check
def fix_auto_fallback_check(content):
    pattern = r"(# Check if we should automatically fallback or ask for confirmation\s+should_auto_fallback = False\s+if current_user\.is_authenticated:).+?(if not should_auto_fallback and fallback_model:)"
    
    replacement = r"""\1
                    try:
                        # Check user's preference for auto-fallback
                        from models import UserChatSettings
                        user_settings = UserChatSettings.query.filter_by(user_id=current_user.id).first()
                        
                        # Create user settings if they don't exist
                        if not user_settings:
                            user_settings = UserChatSettings(user_id=current_user.id)
                            db.session.add(user_settings)
                            db.session.commit()
                            logger.info(f"Created default UserChatSettings for user {current_user.id}")
                        
                        # Safely check the auto_fallback_enabled preference
                        if hasattr(user_settings, 'auto_fallback_enabled') and user_settings.auto_fallback_enabled:
                            should_auto_fallback = True
                            logger.info(f"Auto-fallback enabled for user {current_user.id}")
                        else:
                            logger.info(f"Auto-fallback disabled for user {current_user.id}")
                    except Exception as settings_error:
                        # Log the error but continue with default (no auto-fallback)
                        logger.error(f"Error checking auto-fallback setting: {settings_error}")
                        logger.error(traceback.format_exc())
                
                \2"""
    
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

# Function to fix the fallback notification code
def fix_fallback_notification(content):
    pattern = r"(# Return a streaming response with a model_fallback event\s+def generate_fallback_notification\(\):).+?(return app\.response_class)"
    
    replacement = r"""\1
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
                                yield f'data: {{\"type\":\"error\",\"error\":\"Internal server error\"}}\\n\\n'
                    
                    \2"""
    
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

# Fix the API error response
def fix_api_error_response(content):
    # Find the except block for API errors
    pattern = r"(except Exception as api_error:.+?yield f'data:).+?(return)"
    
    replacement = r"""\1 {{"type": "error", "error": "Connection error while reaching OpenRouter API."}}\\n\\n'
                    \2"""
    
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

# Apply all fixes in sequence
def apply_all_fixes():
    if safe_modify_app_py(fix_auto_fallback_check):
        print("Fixed auto_fallback check code")
    
    if safe_modify_app_py(fix_fallback_notification):
        print("Fixed fallback notification code")
    
    if safe_modify_app_py(fix_api_error_response):
        print("Fixed API error response code")
    
    print("All fixes applied successfully!")

if __name__ == "__main__":
    apply_all_fixes()