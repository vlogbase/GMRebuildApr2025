"""
Test workflow for the hybrid mobile model selector implementation
"""

import subprocess
import sys
import os

def run():
    """
    Run the Flask application to test the hybrid mobile model selector
    """
    print("Starting Flask application to test hybrid mobile model selector...")
    
    # Set environment variable for Flask
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Run the Flask application
    try:
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Error running application: {e}")

if __name__ == "__main__":
    run()