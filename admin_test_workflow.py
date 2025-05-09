"""
Script to test the admin dashboard functionality.
This runs the Flask application with admin access enabled.
"""

import os
import subprocess
import sys
import time
import signal

def run():
    """
    Run tests for admin dashboard functionality.
    """
    print("Starting admin dashboard test...")
    print("This will launch a Flask app with the debug admin tab endpoint.")
    print("Access the debug page at: http://localhost:5000/debug-admin")
    
    try:
        # Run the debug script
        subprocess.run([sys.executable, "debug_admin_tab.py"])
        
    except KeyboardInterrupt:
        print("\nTest terminated by user")
    except Exception as e:
        print(f"Error running admin test: {e}")

if __name__ == "__main__":
    run()