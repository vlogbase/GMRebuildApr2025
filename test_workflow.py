#!/usr/bin/env python3
"""
Test workflow for camera upload functionality
"""

import os
import sys
from app import app

if __name__ == '__main__':
    # Run the Flask application on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)