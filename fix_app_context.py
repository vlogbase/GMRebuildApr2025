#!/usr/bin/env python
"""
Script to fix the application context issue in app.py
This wraps database queries with app.app_context() to prevent
'Working outside of application context' errors.
"""

import os
import re
from datetime import datetime

def backup_file(filename):
    """Create a backup of the file before modifying it."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{filename}.bak.{timestamp}"
    try:
        with open(filename, 'r') as src:
            with open(backup_name, 'w') as dst:
                dst.write(src.read())
        print(f"Backup created: {backup_name}")
        return True
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

def add_app_context_wrapper():
    """
    Find the section in app.py where we need to add app_context and modify it.
    Look for the OpenRouterModel.query.count() outside app_context.
    """
    app_py_path = 'app.py'
    
    # Create backup
    if not backup_file(app_py_path):
        print("Backup failed, aborting.")
        return False
    
    try:
        with open(app_py_path, 'r') as file:
            content = file.read()
        
        # Look for the problematic section
        pattern = r"logger\.info\(\"Performing initial fetch of OpenRouter models at startup\"\)\s*try:\s*# First ensure proper Python imports\s*import traceback\s*from price_updater import fetch_and_store_openrouter_prices\s*from models import OpenRouterModel\s*\s*# Check if we have models in the database\s*model_count = OpenRouterModel\.query\.count\(\)"
        
        # Prepare replacement that adds app context
        replacement = 'logger.info("Performing initial fetch of OpenRouter models at startup")\ntry:\n    # First ensure proper Python imports\n    import traceback\n    from price_updater import fetch_and_store_openrouter_prices\n    from models import OpenRouterModel\n    \n    # Create an application context for database operations\n    with app.app_context():\n        # Check if we have models in the database\n        model_count = OpenRouterModel.query.count()'
        
        # Also fix the second instance
        pattern2 = r"model_count = OpenRouterModel\.query\.count\(\)\s*logger\.info\(f\"Successfully fetched and stored {model_count} OpenRouter models in database\"\)"
        replacement2 = '            with app.app_context():\n                model_count = OpenRouterModel.query.count()\n            logger.info(f"Successfully fetched and stored {model_count} OpenRouter models in database")'
        
        # Apply replacements
        modified_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        modified_content = re.sub(pattern2, replacement2, modified_content, flags=re.DOTALL)
        
        # Write back to the file
        with open(app_py_path, 'w') as file:
            file.write(modified_content)
            
        print(f"Successfully updated {app_py_path} with app context wrappers")
        return True
        
    except Exception as e:
        print(f"Error modifying {app_py_path}: {e}")
        return False

if __name__ == "__main__":
    print("Fixing application context issue in app.py...")
    if add_app_context_wrapper():
        print("✅ Application context fixes successfully applied")
    else:
        print("❌ Failed to apply application context fixes")