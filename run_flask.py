"""
Simple script to run the Flask application for testing in the Replit environment.
"""
import os
import sys
import signal
import subprocess
import time

def run():
    print("Starting Flask application...")
    try:
        # Kill any existing Python processes
        try:
            subprocess.run("pkill -f 'python flask_server.py'", shell=True, check=False)
            time.sleep(2)  # Give time for processes to die
        except Exception as e:
            print(f"Error killing existing processes: {e}")
        
        # Start the Flask server
        process = subprocess.Popen(
            ["python", "flask_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Save the PID for later cleanup
        with open("flask.pid", "w") as f:
            f.write(str(process.pid))
        
        print(f"Flask server started with PID {process.pid}")
        
        # Wait for the server to start
        time.sleep(5)
        
        # Check if server is responding
        try:
            curl_process = subprocess.run(
                ["curl", "-s", "http://localhost:5000/get_models"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            print(f"Server response: {curl_process.stdout[:100]}...")
            if curl_process.returncode != 0:
                print(f"Error: Server not responding. Return code: {curl_process.returncode}")
                print(f"Error output: {curl_process.stderr}")
        except subprocess.TimeoutExpired:
            print("Error: Server request timed out")
        except Exception as e:
            print(f"Error checking server: {e}")
        
        # Stream output from the server
        for line in process.stdout:
            print(line, end="")
            
    except KeyboardInterrupt:
        print("Shutdown requested...")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        print("Cleaning up...")
        try:
            # Read the PID file
            if os.path.exists("flask.pid"):
                with open("flask.pid", "r") as f:
                    pid = int(f.read().strip())
                # Kill the process
                os.kill(pid, signal.SIGTERM)
                print(f"Killed process with PID {pid}")
        except Exception as e:
            print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    run()