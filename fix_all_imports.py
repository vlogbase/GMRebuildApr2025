"""
Fix all import statements in affiliate_blueprint_improved.py

This script will replace all incorrect imports with the correct ones:
- From: from database import User, Affiliate, Commission, ...
- To:   from database import db
        from models import User, Affiliate, Commission, ...
"""

import re
import shutil
from datetime import datetime

def backup_file(filename):
    """Create a backup of the file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{filename}.bak.{timestamp}"
    shutil.copy2(filename, backup_name)
    print(f"Created backup at {backup_name}")

def fix_imports(filename):
    """Fix all model imports in the file"""
    # First make a backup
    backup_file(filename)
    
    # Read file content
    with open(filename, 'r') as f:
        content = f.read()
    
    # Pattern to match model imports from database
    pattern = r'from database import (.*?)(?=\n)'
    
    def replacement(match):
        imports = match.group(1).strip()
        parts = imports.split(', ')
        
        model_parts = []
        has_db = False
        
        for part in parts:
            if part == 'db':
                has_db = True
            else:
                model_parts.append(part)
        
        result = ""
        if has_db:
            result += "from database import db\n"
        if model_parts:
            result += f"from models import {', '.join(model_parts)}"
        
        return result
    
    # Replace all imports
    modified_content = re.sub(pattern, replacement, content)
    
    # Write back to file
    with open(filename, 'w') as f:
        f.write(modified_content)
    
    print(f"Fixed all imports in {filename}")

if __name__ == "__main__":
    fix_imports("affiliate_blueprint_improved.py")