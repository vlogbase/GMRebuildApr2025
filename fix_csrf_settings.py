"""
Script to make CSRF validation more flexible in the application.
This helps with issues that can occur when switching between Cloudflare modes.
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

def update_csrf_config():
    """Update CSRF configuration in app.py to be more robust with proxies"""
    app_py_path = 'app.py'
    
    try:
        # Create backup
        if not backup_file(app_py_path):
            logger.error("Aborting due to backup failure")
            return False
        
        with open(app_py_path, 'r') as f:
            content = f.read()
        
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
    except Exception as e:
        logger.error(f"Error updating CSRF configuration: {e}")
        return False

def main():
    """Apply CSRF configuration changes"""
    logger.info("Starting CSRF configuration update")
    
    # Update CSRF configuration for better handling of proxies
    if not update_csrf_config():
        logger.error("Failed to update CSRF configuration")
        return False
    
    logger.info("CSRF configuration updated successfully")
    return True

if __name__ == "__main__":
    main()