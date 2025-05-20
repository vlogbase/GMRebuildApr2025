"""
Add user_id field to the Affiliate model.

This script modifies the models.py file to add a user_id field to the Affiliate model
so affiliates can be properly linked to users.
"""

import os
import re
from datetime import datetime

def backup_file(filename):
    """Create a backup of a file before modifying it"""
    if os.path.exists(filename):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{filename}.bak_{timestamp}"
        with open(filename, 'r') as src, open(backup_filename, 'w') as dst:
            dst.write(src.read())
        print(f"Created backup: {backup_filename}")
        return True
    return False

def update_affiliate_model():
    """Update the Affiliate model to include a user_id field"""
    # First create a backup
    if not backup_file('models.py'):
        print("Failed to backup models.py")
        return False
    
    # Read the current content
    with open('models.py', 'r') as f:
        content = f.read()
    
    # Find the Affiliate class definition
    affiliate_class_pattern = r'class Affiliate\(db\.Model\):(.*?)# Relationships'
    match = re.search(affiliate_class_pattern, content, re.DOTALL)
    
    if not match:
        print("Could not find Affiliate class definition")
        return False
    
    # Get the class definition part before relationships
    class_def = match.group(1)
    
    # Check if user_id already exists
    if "user_id" in class_def:
        print("user_id field already exists in Affiliate model")
        return True
    
    # Add user_id field after the id field
    updated_class_def = class_def.replace(
        "id = db.Column(db.Integer, primary_key=True)",
        "id = db.Column(db.Integer, primary_key=True)\n    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)"
    )
    
    # Replace the class definition in the content
    updated_content = content.replace(class_def, updated_class_def)
    
    # Write the updated content
    with open('models.py', 'w') as f:
        f.write(updated_content)
    
    print("Successfully added user_id field to Affiliate model")
    return True

if __name__ == "__main__":
    update_affiliate_model()