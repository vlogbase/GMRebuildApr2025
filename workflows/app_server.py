#!/usr/bin/env python3
"""
Main application server workflow
"""
import sys
import os
sys.path.append('..')

def run():
    """Run the main Flask application server"""
    from app import app
    print("🚀 Starting GloriaMundo server...")
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    run()