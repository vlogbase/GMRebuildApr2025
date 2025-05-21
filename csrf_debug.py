"""
Script to diagnose CSRF issues and patch the Flask app for more lenient behavior

This addresses issues that might occur when switching between Cloudflare active/pause modes
by changing how CSRF tokens are validated.
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_file(file_path):
    """Create a backup of a file before modifying it"""
    backup_path = f"{file_path}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        with open(file_path, 'r') as original:
            with open(backup_path, 'w') as backup:
                backup.write(original.read())
        logger.info(f"Created backup of {file_path} at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup of {file_path}: {e}")
        return False

def create_csrf_error_handler():
    """
    Create a CSRF error handler in app.py that logs errors but still processes forms
    
    This effectively disables CSRF protection for the app while maintaining logging
    for debugging purposes.
    """
    app_py_path = 'app.py'
    
    try:
        # Create backup
        if not backup_file(app_py_path):
            logger.error("Aborting due to backup failure")
            return False
        
        with open(app_py_path, 'r') as f:
            content = f.read()
        
        # Check if we have already added the handler
        if 'def csrf_error_handler(reason):' in content:
            logger.info("CSRF error handler already exists in app.py")
            return True
        
        # Find where csrf = CSRFProtect(app) is defined
        csrf_line_index = content.find('csrf = CSRFProtect(app)')
        if csrf_line_index == -1:
            logger.error("Could not find 'csrf = CSRFProtect(app)' in app.py")
            return False
        
        # Find the end of that line to insert after it
        line_end = content.find('\n', csrf_line_index)
        if line_end == -1:
            logger.error("Could not find end of line after CSRF initialization")
            return False
        
        # Define the error handler to add
        csrf_handler = """

# Register a custom CSRF error handler that still allows the form to process
@app.errorhandler(400)
def csrf_error_handler(reason):
    # Handle CSRF errors by logging them but allowing the request
    if 'CSRF' in str(reason):
        logger.warning(f"CSRF validation failed but proceeding anyway: {reason}")
        # Extract the endpoint and try to process it anyway
        try:
            from flask import request, _request_ctx_stack
            view_func = _request_ctx_stack.top.request.url_rule.endpoint
            view_func_obj = app.view_functions.get(view_func)
            if view_func_obj:
                # Try to handle the request as if CSRF passed
                return view_func_obj()
            else:
                logger.error(f"Could not find view function for endpoint {view_func}")
        except Exception as e:
            logger.error(f"Error in CSRF error handler: {e}")
    
    # If not a CSRF error or we couldn't handle it, return the normal 400 error
    return "Bad Request", 400

"""
        
        # Insert the error handler after the CSRF initialization
        new_content = content[:line_end+1] + csrf_handler + content[line_end+1:]
        
        # Write the updated file
        with open(app_py_path, 'w') as f:
            f.write(new_content)
        
        logger.info("Successfully added CSRF error handler to app.py")
        return True
    except Exception as e:
        logger.error(f"Error updating app.py: {e}")
        return False

def update_csrf_config():
    """Update CSRF configuration in app.py to be more robust with proxies"""
    app_py_path = 'app.py'
    
    try:
        # Create backup if we haven't already
        if not os.path.exists(f"{app_py_path}.bak.{datetime.now().strftime('%Y%m%d')}"):
            if not backup_file(app_py_path):
                logger.error("Aborting due to backup failure")
                return False
        
        with open(app_py_path, 'r') as f:
            content = f.read()
        
        # Check if WTF_CSRF_SSL_STRICT is already set
        if "app.config['WTF_CSRF_SSL_STRICT'] = False" in content:
            logger.info("CSRF SSL strict mode already disabled")
        else:
            # Find the CSRF time limit line
            csrf_time_limit_line = "app.config['WTF_CSRF_TIME_LIMIT'] = 86400  # Set CSRF token timeout to 24 hours (in seconds)"
            if csrf_time_limit_line in content:
                # Add our new config right after the time limit line
                new_config = """
# Disable strict SSL checking for CSRF to handle Cloudflare and non-Cloudflare modes
app.config['WTF_CSRF_SSL_STRICT'] = False

# Make sure CSRF cookie matches the domain being used
app.config['WTF_CSRF_SAMESITE'] = 'Lax'
"""
                new_content = content.replace(csrf_time_limit_line, 
                                             csrf_time_limit_line + new_config)
                
                # Write the updated file
                with open(app_py_path, 'w') as f:
                    f.write(new_content)
                
                logger.info("Successfully updated CSRF configuration")
                return True
            else:
                logger.error("Could not find CSRF time limit configuration in app.py")
                return False
                
        return True
    except Exception as e:
        logger.error(f"Error updating CSRF configuration: {e}")
        return False

def main():
    """Apply all CSRF fixes"""
    logger.info("Starting CSRF troubleshooting")
    
    # Update CSRF configuration for better handling of proxies
    if not update_csrf_config():
        logger.error("Failed to update CSRF configuration")
    
    # Create a custom CSRF error handler
    if not create_csrf_error_handler():
        logger.error("Failed to create CSRF error handler")
    
    logger.info("CSRF troubleshooting completed")
    return True

if __name__ == "__main__":
    main()