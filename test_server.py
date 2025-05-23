#!/usr/bin/env python3
"""
Simple test server to check if the account page works
"""
import sys
import os
sys.path.append('.')

from app import app

if __name__ == "__main__":
    print("Starting test server...")
    app.run(host='0.0.0.0', port=5000, debug=True)