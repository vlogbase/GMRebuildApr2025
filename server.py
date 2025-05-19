"""
Simple server startup script for deployment
This ensures the app consistently runs on port 3000
"""
from app import app

if __name__ == "__main__":
    # Always use port 3000 for deployment
    port = 3000
    print(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port)