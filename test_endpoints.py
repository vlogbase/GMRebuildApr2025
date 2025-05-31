#!/usr/bin/env python3
"""
Quick test script to verify API endpoints are working after fixing mismatches
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app import app

if __name__ == '__main__':
    print("Starting test server for endpoint verification...")
    print("Fixed endpoints:")
    print("- /conversations (GET) - fetch conversations")
    print("- /chat (POST) - send messages") 
    print("- /upload_file (POST) - file uploads")
    print("- /api/conversations (POST) - create new conversation")
    print("- /api/conversations/<id>/messages (GET) - load conversation messages")
    print("- /get_preferences (GET) - user preferences")
    print("- /save_preference (POST) - save model preferences")
    print("- /reset_preferences (POST) - reset preferences")
    print("- /api/get_model_prices (GET) - model pricing data")
    
    # Start simplified server
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)