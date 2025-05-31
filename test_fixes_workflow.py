#!/usr/bin/env python3
"""
Test workflow to verify the 4 mobile fixes
"""

import subprocess
import sys
import os

def run():
    """Start the Flask app to test the fixes"""
    try:
        # Change to the project directory
        os.chdir('/home/runner/workspace')
        
        # Start the Flask application
        print("Starting Flask application...")
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error starting app: {e}")

if __name__ == "__main__":
    run()