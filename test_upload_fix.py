#!/usr/bin/env python3
"""
Quick test to verify upload functionality and fix CSRF issues
"""

import sys
import os
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app import app

if __name__ == '__main__':
    print("Starting test server for upload debugging...")
    
    # Temporarily disable CSRF for testing
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['TESTING'] = True
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)