"""
Test file to validate our JavaScript fixes
"""

import time
import webbrowser
import subprocess
import sys
import os

def main():
    print("Starting Flask server for testing...")
    
    # Run the Flask app in the background
    server_process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    # Give the server a moment to start
    time.sleep(3)
    
    print("Server started. You can access it at http://localhost:5000")
    print("You can CTRL+C to stop the server when done testing")
    
    try:
        # Keep the script running
        while True:
            # Print output from the server
            line = server_process.stdout.readline()
            if line:
                print(line.decode('utf-8').strip())
            
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping server...")
        server_process.terminate()
        server_process.wait()
        print("Server stopped.")

if __name__ == "__main__":
    main()