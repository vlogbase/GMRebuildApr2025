#!/usr/bin/env python3
"""
Simple test workflow to run the Flask application and test the reset functionality
"""

import subprocess
import sys
import os

def main():
    """Run the Flask application for testing"""
    print("Starting Flask application for testing...")
    
    # Set environment variables if needed
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', '1')
    
    # Start the Flask application
    try:
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\nShutting down Flask application...")
    except Exception as e:
        print(f"Error running Flask application: {e}")

if __name__ == "__main__":
    main()