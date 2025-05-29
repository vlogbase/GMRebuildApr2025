#!/usr/bin/env python3
"""
Test workflow for the model selection fixes
"""

import subprocess
import sys

def run():
    """
    Run the Flask application to test the model selection improvements
    """
    print("Starting Flask application with model selection fixes...")
    
    try:
        # Run the Flask app
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\nShutting down Flask application...")
    except Exception as e:
        print(f"Error running Flask application: {e}")

if __name__ == "__main__":
    run()