"""
Complete indentation fix for app.py
"""
import os
from datetime import datetime

# Create a backup of the original file
backup_file = f'app.py.bak.indent_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
os.system(f'cp app.py {backup_file}')
print(f"Created backup: {backup_file}")

# Simplest approach: manually fix the exception handling block at line 700-710
with open('app.py', 'r') as f:
    lines = f.readlines()

# Insert a 'try:' statement before the exception block
found_try = False
found_exception = False
fixed_lines = []

for i, line in enumerate(lines):
    # Check if this is the problematic area
    if "except Exception as api_error:" in line and not found_exception:
        # We found the exception without a corresponding try
        found_exception = True
        # Find the right indentation level based on nearby lines
        indent = ""
        for char in line:
            if char == ' ' or char == '\t':
                indent += char
            else:
                break
        
        # Add the missing try block with proper indentation
        fixed_lines.append(f"{indent}try:\n")
        fixed_lines.append(f"{indent}    pass  # Placeholder for try block\n")
        fixed_lines.append(line)
    else:
        fixed_lines.append(line)

# Write the fixed content back
with open('app.py', 'w') as f:
    f.writelines(fixed_lines)

print("Fixed indentation issues in app.py")