"""
Fix for affiliate import issues

This script fixes import statements in the affiliate blueprint
to ensure models are properly imported from models.py
"""

import re
import shutil
import os
from datetime import datetime

def backup_file(filename):
    """Create a backup of a file before modifying it"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{filename}.bak.{timestamp}"
    
    try:
        shutil.copy2(filename, backup_name)
        print(f"Created backup: {backup_name}")
        return True
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

def fix_imports(filename):
    """
    Fix import statements in the file
    Replace 'from database import User, ...' with proper imports
    """
    try:
        # Read the file content
        with open(filename, 'r') as f:
            content = f.read()
        
        # Create a backup
        if not backup_file(filename):
            print("Skipping file modification due to backup failure")
            return False
        
        # Pattern to find imports from database that include models
        pattern = r'from database import (.*?)(?=\n)'
        
        def replace_import(match):
            """Replace import statement with correct format"""
            imports = match.group(1).strip()
            
            if 'db' in imports and any(model in imports for model in ['User', 'Affiliate', 'Commission', 'CustomerReferral', 'Transaction']):
                # Import db from database and models from models
                models = []
                modules = imports.split(', ')
                
                for module in modules:
                    if module == 'db':
                        continue
                    models.append(module)
                
                return f"from database import db\nfrom models import {', '.join(models)}"
            
            # If just db is imported, leave it alone
            return match.group(0)
        
        # Replace all model imports
        modified_content = re.sub(pattern, replace_import, content)
        
        # Write the modified content back to the file
        with open(filename, 'w') as f:
            f.write(modified_content)
        
        print(f"Successfully updated import statements in {filename}")
        return True
    
    except Exception as e:
        print(f"Error updating file: {e}")
        return False

if __name__ == "__main__":
    filename = "affiliate_blueprint_improved.py"
    fix_imports(filename)