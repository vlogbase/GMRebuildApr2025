#!/usr/bin/env python3
"""
Test workflow to verify the JavaScript fixes
"""

import os
import sys
sys.path.append('.')

from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)