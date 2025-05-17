"""
Script to apply a focused fix for the model fallback confirmation feature.
This adds the auto_fallback_enabled field to the database and ensures the
fallback confirmation works properly without touching other code.
"""
import os
import sys
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='fix_fallback.log'
)
logger = logging.getLogger(__name__)

def backup_file(filename):
    """Create a backup of a file before modifying it"""
    backup_name = f"{filename}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        with open(filename, 'r') as src, open(backup_name, 'w') as dst:
            dst.write(src.read())
        logger.info(f"Created backup: {backup_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup of {filename}: {e}")
        return False

def ensure_column_in_userchat_settings():
    """
    Ensure the auto_fallback_enabled column exists in the UserChatSettings table.
    """
    try:
        # Create app context to interact with database
        from app import app, db
        from sqlalchemy import inspect, text

        with app.app_context():
            # Check if the user_chat_settings table exists
            inspector = inspect(db.engine)
            if 'user_chat_settings' not in inspector.get_table_names():
                logger.warning("user_chat_settings table does not exist, creating it...")
                from models import UserChatSettings
                db.create_all()
                logger.info("Created user_chat_settings table.")
                return True

            # Check if auto_fallback_enabled column exists
            columns = [col['name'] for col in inspector.get_columns('user_chat_settings')]
            if 'auto_fallback_enabled' in columns:
                logger.info("auto_fallback_enabled column already exists in user_chat_settings table.")
                return True

            # Add the column with appropriate SQL for PostgreSQL
            logger.info("Adding auto_fallback_enabled column to user_chat_settings table...")
            with db.engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE user_chat_settings ADD COLUMN auto_fallback_enabled BOOLEAN DEFAULT FALSE NOT NULL"
                ))
                conn.commit()
            
            logger.info("Successfully added auto_fallback_enabled column to user_chat_settings table.")
            return True
        
    except Exception as e:
        logger.error(f"Error ensuring auto_fallback_enabled column: {e}")
        logger.error(traceback.format_exc())
        return False

def add_fallback_apis():
    """
    Add API routes for auto_fallback preference if they don't exist.
    """
    try:
        # Check if the API routes for fallback preferences already exist
        from app import app
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        
        chat_settings_route = '/api/user/chat_settings'
        if chat_settings_route in routes:
            logger.info(f"API route {chat_settings_route} already exists.")
            return True
        
        # We'll add the route by creating a new file that will be imported
        fallback_api_file = 'fallback_api.py'
        backup_file(fallback_api_file) if os.path.exists(fallback_api_file) else None
        
        with open(fallback_api_file, 'w') as f:
            f.write("""'''
API routes for model fallback confirmation feature.
'''
from flask import request, jsonify
from app import app, db
from models import UserChatSettings
from flask_login import current_user, login_required
import logging

logger = logging.getLogger(__name__)

@app.route('/api/user/chat_settings', methods=['GET', 'POST'])
@login_required
def user_chat_settings():
    '''Get or update user chat settings including auto_fallback_enabled'''
    if request.method == 'POST':
        try:
            data = request.json
            
            # Get current settings or create new ones
            settings = UserChatSettings.query.filter_by(user_id=current_user.id).first()
            if not settings:
                settings = UserChatSettings(user_id=current_user.id)
                db.session.add(settings)
            
            # Update the auto_fallback_enabled setting if present
            if 'auto_fallback_enabled' in data:
                auto_fallback = bool(data['auto_fallback_enabled'])
                settings.auto_fallback_enabled = auto_fallback
                logger.info(f"Setting auto_fallback_enabled to {auto_fallback} for user {current_user.id}")
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'settings': {
                    'auto_fallback_enabled': settings.auto_fallback_enabled
                }
            })
        except Exception as e:
            logger.error(f"Error updating chat settings: {e}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            })
    else:
        try:
            # Get current settings or return defaults
            settings = UserChatSettings.query.filter_by(user_id=current_user.id).first()
            
            if settings:
                # Handle the case where auto_fallback_enabled might not exist yet
                auto_fallback = False
                if hasattr(settings, 'auto_fallback_enabled'):
                    auto_fallback = settings.auto_fallback_enabled
                
                return jsonify({
                    'success': True,
                    'settings': {
                        'auto_fallback_enabled': auto_fallback
                    }
                })
            else:
                # Return default settings
                return jsonify({
                    'success': True,
                    'settings': {
                        'auto_fallback_enabled': False
                    }
                })
        except Exception as e:
            logger.error(f"Error getting chat settings: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            })
""")
        logger.info(f"Created {fallback_api_file} with API routes for model fallback preferences.")
        
        # Update app.py to import the fallback_api module
        if not update_app_imports():
            logger.warning("Failed to update app.py imports. Manual import of fallback_api.py may be needed.")
        
        return True
    
    except Exception as e:
        logger.error(f"Error adding fallback API routes: {e}")
        logger.error(traceback.format_exc())
        return False

def update_app_imports():
    """
    Update app.py to import the fallback API module.
    """
    try:
        # Backup app.py first
        if not backup_file('app.py'):
            return False
        
        # Read app.py content
        with open('app.py', 'r') as f:
            content = f.readlines()
        
        # Find a good place to add the import
        import_line = "import fallback_api  # Import model fallback APIs\n"
        
        # Look for the last import statement
        import_index = -1
        for i, line in enumerate(content):
            if line.startswith('import ') or line.startswith('from '):
                import_index = i
        
        if import_index >= 0:
            # Add our import after the last import statement
            content.insert(import_index + 1, import_line)
            
            # Write the updated content
            with open('app.py', 'w') as f:
                f.writelines(content)
            
            logger.info("Updated app.py imports to include fallback_api module.")
            return True
        else:
            logger.warning("Could not find a suitable place to add import in app.py.")
            return False
        
    except Exception as e:
        logger.error(f"Error updating app.py imports: {e}")
        logger.error(traceback.format_exc())
        return False

def update_account_template():
    """
    Update the account template to include auto-fallback preference setting.
    """
    try:
        account_template = 'templates/account.html'
        
        # Check if the file exists
        if not os.path.exists(account_template):
            logger.warning(f"{account_template} does not exist. Skipping template update.")
            return False
        
        # Backup the template
        if not backup_file(account_template):
            return False
        
        # Read the template content
        with open(account_template, 'r') as f:
            content = f.read()
        
        # Check if the auto-fallback setting is already present
        if 'auto_fallback_enabled' in content:
            logger.info("Auto-fallback setting already exists in account template.")
            return True
        
        # Find a good place to add the setting
        # Look for the end of a settings section or tab
        settings_section_end = content.find('</div><!-- End of settings section')
        if settings_section_end == -1:
            # Try another common pattern
            settings_section_end = content.find('</div><!-- End of tab-pane')
        
        if settings_section_end != -1:
            # HTML for the auto-fallback setting
            auto_fallback_html = """
                <div class="form-group mt-4">
                    <div class="custom-control custom-switch">
                        <input type="checkbox" class="custom-control-input" id="autoFallbackEnabled" name="auto_fallback_enabled" value="1">
                        <label class="custom-control-label" for="autoFallbackEnabled">
                            Automatically fall back when models are unavailable
                        </label>
                        <small class="form-text text-muted">
                            When enabled, if your selected model is unavailable, the system will automatically use the best available alternative.
                            When disabled, you'll be asked to confirm before using a different model.
                        </small>
                    </div>
                </div>
            """
            
            # Insert the auto-fallback setting before the section end
            updated_content = content[:settings_section_end] + auto_fallback_html + content[settings_section_end:]
            
            # Write the updated content
            with open(account_template, 'w') as f:
                f.write(updated_content)
            
            logger.info("Updated account template with auto-fallback setting.")
            return True
        else:
            logger.warning("Could not find a suitable place to add auto-fallback setting in account template.")
            return False
        
    except Exception as e:
        logger.error(f"Error updating account template: {e}")
        logger.error(traceback.format_exc())
        return False

def add_account_js():
    """
    Add JavaScript to handle the auto-fallback preference setting.
    """
    try:
        account_js_file = 'static/js/account_fallback.js'
        
        # Create the JavaScript file
        with open(account_js_file, 'w') as f:
            f.write("""/**
 * JavaScript to handle auto-fallback preference setting in the account page.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get the auto-fallback checkbox
    const autoFallbackCheckbox = document.getElementById('autoFallbackEnabled');
    if (!autoFallbackCheckbox) return;
    
    // Load the current setting on page load
    loadAutoFallbackSetting();
    
    // Add event listener to save the setting when changed
    autoFallbackCheckbox.addEventListener('change', saveAutoFallbackSetting);
    
    /**
     * Load the current auto-fallback setting.
     */
    function loadAutoFallbackSetting() {
        fetch('/api/user/chat_settings')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.settings) {
                    autoFallbackCheckbox.checked = !!data.settings.auto_fallback_enabled;
                }
            })
            .catch(error => {
                console.error('Error loading auto-fallback setting:', error);
            });
    }
    
    /**
     * Save the auto-fallback setting.
     */
    function saveAutoFallbackSetting() {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        
        fetch('/api/user/chat_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                auto_fallback_enabled: autoFallbackCheckbox.checked
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error('Error saving auto-fallback setting:', data.error);
                // Reset the checkbox to its previous state
                loadAutoFallbackSetting();
            }
        })
        .catch(error => {
            console.error('Error saving auto-fallback setting:', error);
            // Reset the checkbox to its previous state
            loadAutoFallbackSetting();
        });
    }
});
""")
        
        logger.info(f"Created {account_js_file} to handle auto-fallback preference setting.")
        
        # Now update the account template to include this JavaScript file
        account_template = 'templates/account.html'
        if os.path.exists(account_template):
            # Backup the template
            if not backup_file(account_template):
                return False
            
            # Read the template content
            with open(account_template, 'r') as f:
                content = f.read()
            
            # Check if the JavaScript file is already included
            if 'account_fallback.js' in content:
                logger.info("JavaScript file already included in account template.")
                return True
            
            # Find the scripts block
            scripts_tag = "{% block scripts %}"
            scripts_end_tag = "{% endblock %}"
            
            scripts_start = content.find(scripts_tag)
            scripts_end = content.find(scripts_end_tag, scripts_start)
            
            if scripts_start != -1 and scripts_end != -1:
                # Script tag to include our JavaScript file
                script_include = '    <script src="{{ url_for(\'static\', filename=\'js/account_fallback.js\') }}"></script>\n'
                
                # Insert the script include before the end of the scripts block
                updated_content = content[:scripts_end] + script_include + content[scripts_end:]
                
                # Write the updated content
                with open(account_template, 'w') as f:
                    f.write(updated_content)
                
                logger.info("Updated account template to include account_fallback.js.")
                return True
            else:
                logger.warning("Could not find scripts block in account template.")
                return False
        else:
            logger.warning(f"{account_template} does not exist. Skipping JavaScript include.")
            return False
        
    except Exception as e:
        logger.error(f"Error adding account JavaScript: {e}")
        logger.error(traceback.format_exc())
        return False

def fix_model_check():
    """
    Fix the model availability check in app.py to use the auto_fallback_enabled setting.
    """
    try:
        # Backup app.py first
        if not backup_file('app.py'):
            return False
        
        # Read app.py content
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Replace the automatic fallback with the confirmation dialog
        auto_fallback_code = """
                # Check if we should automatically fallback or ask for confirmation
                should_auto_fallback = False
                if current_user.is_authenticated:
                    try:
                        # Check user's preference for auto-fallback
                        from models import UserChatSettings
                        user_settings = UserChatSettings.query.filter_by(user_id=current_user.id).first()
                        
                        # Safely check the auto_fallback_enabled preference
                        if user_settings and hasattr(user_settings, 'auto_fallback_enabled') and user_settings.auto_fallback_enabled:
                            should_auto_fallback = True
                            logger.info(f"Auto-fallback enabled for user {current_user.id}")
                        else:
                            logger.info(f"Auto-fallback disabled for user {current_user.id}")
                    except Exception as settings_error:
                        # Log the error but continue with default (no auto-fallback)
                        logger.error(f"Error checking auto-fallback setting: {settings_error}")
                
                if not should_auto_fallback and fallback_model:
                    # Use the streaming response format to indicate fallback is needed but requires confirmation
                    logger.info(f"Model {openrouter_model} unavailable - suggesting fallback to {fallback_model}")
                    
                    # Find the human-readable names for both models
                    original_model_name = openrouter_model.split('/')[-1] if '/' in openrouter_model else openrouter_model
                    fallback_model_name = fallback_model.split('/')[-1] if '/' in fallback_model else fallback_model
                    
                    # Return a streaming response with a model_fallback event
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
                                error_json = json.dumps({
                                    'type': 'error', 
                                    'error': 'Failed to generate fallback notification'
                                })
                                yield f'data: {error_json}\\n\\n'
                            except Exception as e:
                                logger.error(f"Critical failure in fallback notification system: {e}")
                                yield f'data: {{\"type\":\"error\",\"error\":\"Internal server error\"}}\\n\\n'
                    
                    return app.response_class(
                        generate_fallback_notification(),
                        mimetype='text/event-stream'
                    )
"""
        
        # Determine how to apply the changes based on presence of key phrases
        if "Check if we should automatically fallback or ask for confirmation" in content:
            logger.info("Auto-fallback code already present in app.py.")
            return True
        
        # Look for the pattern right before where our code should go
        pattern_before = "fallback_model = model_validator.get_fallback_model"
        pattern_after = "# Use the fallback model"
        
        start_idx = content.find(pattern_before)
        if start_idx == -1:
            logger.warning("Could not find the insertion point for auto-fallback code in app.py.")
            return False
        
        # Find the end of the get_fallback_model section
        end_pattern_search = content.find(pattern_after, start_idx)
        if end_pattern_search == -1:
            # Try an alternative approach - look for the next logical step
            end_pattern_search = content.find("openrouter_model = fallback_model", start_idx)
        
        if end_pattern_search == -1:
            logger.warning("Could not find the end of the fallback model section in app.py.")
            return False
        
        # Find the end of the line containing the get_fallback_model call
        line_end = content.find(')', start_idx)
        if line_end == -1 or line_end > end_pattern_search:
            line_end = content.find('\n', start_idx)
        
        if line_end == -1:
            logger.warning("Could not find the end of the get_fallback_model line in app.py.")
            return False
        
        # Insert our auto-fallback code after the get_fallback_model call
        updated_content = content[:line_end + 1] + auto_fallback_code + content[end_pattern_search:]
        
        # Write the updated content
        with open('app.py', 'w') as f:
            f.write(updated_content)
        
        logger.info("Updated app.py with auto-fallback code.")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing model check in app.py: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """
    Apply all fixes for the model fallback confirmation feature.
    """
    logger.info("Starting model fallback confirmation feature fixes...")
    
    # 1. Ensure the auto_fallback_enabled column exists in the database
    if not ensure_column_in_userchat_settings():
        logger.error("Failed to ensure auto_fallback_enabled column in database.")
        return False
    
    # 2. Add API routes for auto-fallback preference
    if not add_fallback_apis():
        logger.error("Failed to add API routes for auto-fallback preference.")
        return False
    
    # 3. Update the account template
    if not update_account_template():
        logger.warning("Failed to update account template. Feature will still work, but users can't change the setting.")
    
    # 4. Add JavaScript for the account page
    if not add_account_js():
        logger.warning("Failed to add account JavaScript. Feature will still work, but users can't change the setting.")
    
    # 5. Fix the model availability check in app.py
    if not fix_model_check():
        logger.error("Failed to fix model check in app.py.")
        return False
    
    logger.info("Successfully applied all fixes for the model fallback confirmation feature.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)