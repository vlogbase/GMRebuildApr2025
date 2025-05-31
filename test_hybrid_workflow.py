#!/usr/bin/env python3
"""
Test workflow for the mobile button fix
"""

import subprocess
import sys
import os

def main():
    """
    Run the Flask application for testing mobile buttons
    """
    print("Starting Flask application for mobile button testing...")
    print("Application will be available at http://0.0.0.0:5000")
    
    # Change to the correct directory and run the Flask app
    os.chdir('/home/runner/workspace')
    
    # Run the Flask application
    subprocess.run([sys.executable, 'app.py'], check=False)

if __name__ == '__main__':
    main()