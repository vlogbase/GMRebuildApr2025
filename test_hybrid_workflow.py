#!/usr/bin/env python3
"""
Test workflow for the hybrid mobile/desktop model selector
"""

import os
import sys

# Add the current directory to Python path so we can import app
sys.path.insert(0, os.getcwd())

def main():
    """Run the Flask application"""
    try:
        from app import app
        print("Starting Flask application for mobile model selector testing...")
        print("Application will be available at http://0.0.0.0:5000")
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()