"""
Test workflow for pricing table colors
"""
import os
import sys
from app import app

if __name__ == '__main__':
    print("Starting Flask app to test pricing table colors...")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)