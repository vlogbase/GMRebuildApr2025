#!/usr/bin/env python3
"""
Test workflow for model selector functionality
"""

import subprocess
import sys
import os

def run():
    """Run the Flask application for testing"""
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    try:
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\nStopped")

if __name__ == "__main__":
    run()