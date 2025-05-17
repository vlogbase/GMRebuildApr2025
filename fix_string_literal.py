"""
Fix unterminated string literals in app.py
"""
import re
import os
import logging
from datetime import datetime

# Create a backup
backup_file = f'app.py.bak.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
os.system(f'cp app.py {backup_file}')
print(f"Created backup: {backup_file}")

# Read the file
with open('app.py', 'r') as f:
    content = f.read()

# Fix the unterminated string literals
fixed_content = content.replace(
    'yield f\'data: {{"type": "error", "error": "Connection error while reaching OpenRouter API."}}\n\n\'',
    'yield f\'data: {{"type": "error", "error": "Connection error while reaching OpenRouter API."}}\n\n\''
)

# Another pattern to fix
fixed_content = fixed_content.replace(
    'yield f\'data: {{"type": "error", "error": "Connection error while reaching OpenRouter API."}}\n\n',
    'yield f\'data: {{"type": "error", "error": "Connection error while reaching OpenRouter API."}}\n\n\''
)

# Fix all instances where the string literal is incorrectly formatted
pattern = r"(yield f'data:.+}})(\s*\n\s*)'()"
fixed_content = re.sub(pattern, r'\1\\n\\n\'', fixed_content)

# Write the fixed content back
with open('app.py', 'w') as f:
    f.write(fixed_content)

print("Fixed unterminated string literals in app.py")