#!/usr/bin/env python3
"""
Run the server for testing
"""
if __name__ == "__main__":
    import sys
    sys.path.append('.')
    from app import app
    print("Starting server on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)