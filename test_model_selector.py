#!/usr/bin/env python3
"""
Test workflow for the model selector closing mechanism fix
"""

import subprocess
import sys
import os

def run():
    """
    Run the Flask application to test the model selector closing functionality
    """
    # Change to the project directory
    os.chdir('.')
    
    # Set environment variables
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Run the Flask application
    try:
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\nApplication stopped.")
    except Exception as e:
        print(f"Error running application: {e}")

if __name__ == "__main__":
    run()