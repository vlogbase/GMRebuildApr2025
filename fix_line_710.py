"""
Fix indentation issue around line 710 in app.py
"""
import os
from datetime import datetime

# Create a backup
backup_file = f"app.py.bak.fix_20250517_{datetime.now().strftime('%H%M%S')}"
os.system(f"cp app.py {backup_file}")
print(f"Created backup: {backup_file}")

# Read all the lines
with open('app.py', 'r') as f:
    lines = f.readlines()

# Look for the specific section with indentation issues
looking_for_line = "if response.status_code != 200:"
problematic_line_found = False
fixed_lines = []

for i, line in enumerate(lines):
    if looking_for_line in line:
        problematic_line_found = True
        # Found the problematic line, now fix it
        fixed_line = line.replace("if response.status_code != 200:", "            if response.status_code != 200:")
        fixed_lines.append(fixed_line)
        
        # We need to adjust the indentation of the following lines too
        j = i + 1
        while j < len(lines) and (lines[j].strip() == "" or lines[j].lstrip().startswith("print") or lines[j].lstrip().startswith("logger") or lines[j].lstrip().startswith("#") or lines[j].lstrip().startswith("if ")):
            if lines[j].strip():  # Skip empty lines
                indent = "            "  # Match the indentation of the fixed if statement
                fixed_lines.append(f"{indent}{lines[j].lstrip()}")
            else:
                fixed_lines.append(lines[j])  # Keep empty lines as is
            j += 1
        
        # Add the next line with proper indentation if we didn't reach the end
        if j < len(lines):
            fixed_lines.append(lines[j])
        
        # Skip all the lines we already processed
        i = j
    else:
        fixed_lines.append(line)

# Write the fixed lines back to the file
if problematic_line_found:
    with open('app.py', 'w') as f:
        f.writelines(fixed_lines)
    print("Successfully fixed indentation issues around line 710")
else:
    print("Could not find the problematic line containing 'if response.status_code != 200:'")