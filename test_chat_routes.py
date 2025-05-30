#!/usr/bin/env python3
"""
Test script to verify the new chat route functionality
"""

import subprocess
import time
import requests
import sys

def test_routes():
    """Test the chat routes"""
    print("Testing chat route implementation...")
    
    # Start the Flask app in background
    print("Starting Flask application...")
    proc = subprocess.Popen(['python', 'main.py'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
    
    # Wait for the app to start
    time.sleep(8)
    
    try:
        # Test the main route
        print("Testing main route...")
        response = requests.get('http://localhost:5000/', timeout=10)
        print(f"Main route status: {response.status_code}")
        
        # Test the new chat route (should redirect to login for unauthenticated users)
        print("Testing chat route...")
        response = requests.get('http://localhost:5000/chat/123', 
                              allow_redirects=False, timeout=10)
        print(f"Chat route status: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ Chat route working - redirects unauthenticated users to login")
        elif response.status_code == 404:
            print("❌ Chat route not found - route not properly registered")
        else:
            print(f"Chat route returned unexpected status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error testing routes: {e}")
    finally:
        # Clean up
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    test_routes()