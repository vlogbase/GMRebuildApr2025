#!/usr/bin/env python3
"""
Simple test workflow for the metadata display fix
"""
import subprocess
import sys

def run():
    """Run the Flask application for testing"""
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("Server stopped")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()