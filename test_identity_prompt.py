#!/usr/bin/env python3
"""
Test Identity Prompt Preference Feature

This script starts the Flask application to test the new identity prompt preference functionality.
"""

if __name__ == "__main__":
    from app import app
    app.run(host='0.0.0.0', port=5000, debug=True)