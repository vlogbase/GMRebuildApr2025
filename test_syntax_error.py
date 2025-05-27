#!/usr/bin/env python3
"""
Test workflow to check the syntax error in script.js
"""

import subprocess
import sys
import os

def run():
    """
    Run the Flask application to test the syntax error
    """
    try:
        # Change to the correct directory
        os.chdir('/home/runner/workspace')
        
        # Run the Flask application
        print("Starting Flask application...")
        subprocess.run([sys.executable, 'app.py'], check=True)
        
    except KeyboardInterrupt:
        print("\nApplication stopped.")
    except Exception as e:
        print(f"Error running application: {e}")

if __name__ == "__main__":
    run()