#!/usr/bin/env python3
"""
Server workflow for testing the account page
"""
import sys
import os
sys.path.append('..')

from app import app

def run():
    """Run the Flask server"""
    print("Starting server for account page testing...")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()