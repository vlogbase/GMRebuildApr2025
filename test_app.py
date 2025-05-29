#!/usr/bin/env python3
"""
Simple test server to verify metadata display fix
"""

if __name__ == "__main__":
    import app
    app.app.run(host="0.0.0.0", port=5000, debug=True)