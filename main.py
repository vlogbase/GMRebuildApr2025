"""
Main entry point for Replit deployment.
This file is used by Replit for deployments.
"""
import os
import sys
from werkzeug.middleware.proxy_fix import ProxyFix

# Import Flask app directly from app.py
# This is what Replit's gunicorn server looks for
from app import app

# Apply ProxyFix to ensure proper handling of proxied requests
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_proto=1,  # Number of values to trust for X-Forwarded-Proto
    x_host=1,   # Number of values to trust for X-Forwarded-Host
    x_prefix=1, # Number of values to trust for X-Forwarded-Prefix
    x_for=1     # Number of values to trust for X-Forwarded-For
)

# Ensure PORT is set to 3000 for Replit deployments
os.environ["PORT"] = "3000"

# This part is used when running the file directly (not through gunicorn)
if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 3000))
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        print(f"Error starting the application: {e}")
        sys.exit(1)