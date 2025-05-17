"""
Script to fix indentation errors in app.py.
"""
import re
import os
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   filename='fix_indentation.log')
logger = logging.getLogger(__name__)

def fix_app_py():
    """Fix indentation errors in app.py"""
    try:
        # Create a backup of the original file
        backup_filename = f'app.py.bak.indent_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        os.system(f'cp app.py {backup_filename}')
        logger.info(f"Created backup of app.py at {backup_filename}")
        
        # Read the current content with line numbers for better error reporting
        with open('app.py', 'r') as f:
            lines = f.readlines()
        
        # Write a clean version with proper indentation
        with open('app.py', 'w') as f:
            in_chat_endpoint = False
            in_try_block = False
            previous_line_empty = False
            
            for i, line in enumerate(lines):
                line_num = i + 1
                try:
                    # Check if we're entering the chat endpoint
                    if "@app.route('/chat'" in line:
                        in_chat_endpoint = True
                    
                    # Check for the main try block in chat endpoint
                    if in_chat_endpoint and "try:" in line and not in_try_block:
                        in_try_block = True
                    
                    # Handle specific indentation issues around line 701
                    if line_num in range(695, 710):
                        if line.strip().startswith("except Exception as api_error:"):
                            # Fix indentation of the except block
                            f.write("        except Exception as api_error:\n")
                            continue
                        elif in_try_block and "logger.error" in line and line_num in range(701, 704):
                            # Fix indentation of error logging in the except block
                            f.write("            " + line.lstrip())
                            continue
                        elif in_try_block and "abort(500" in line and line_num in range(704, 707):
                            # Fix indentation of abort in the except block
                            f.write("            " + line.lstrip())
                            continue
                    
                    # Handle other problematic areas
                    if "unexpected indentation" in line or "unindent does not match" in line:
                        # Log the problematic line for debugging
                        logger.warning(f"Potentially problematic line {line_num}: {line.strip()}")
                        
                        # Adjust indentation based on context
                        if in_try_block:
                            # Most lines in the try block should have at least 8 spaces (4 for the function, 4 for try)
                            f.write("        " + line.lstrip())
                            continue
                    
                    # Write the line as is if no specific fixes needed
                    f.write(line)
                    
                    # Track empty lines (may affect indentation)
                    previous_line_empty = line.strip() == ""
                    
                    # Check if we're exiting the chat endpoint (simplified detection)
                    if in_chat_endpoint and line.startswith("@app.route") and "/chat" not in line:
                        in_chat_endpoint = False
                        in_try_block = False
                
                except Exception as e:
                    logger.error(f"Error processing line {line_num}: {line.strip()}")
                    logger.error(traceback.format_exc())
                    # Write the original line in case of error
                    f.write(line)
        
        logger.info("Fixed indentation errors in app.py")
        return True
    
    except Exception as e:
        logger.error(f"Failed to fix app.py: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = fix_app_py()
    if success:
        print("Successfully fixed indentation errors in app.py")
    else:
        print("Failed to fix indentation errors. See fix_indentation.log for details.")