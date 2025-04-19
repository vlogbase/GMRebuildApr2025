#!/bin/bash

# Print startup message
echo "Starting Flask server with Google OAuth support..."
echo "Make sure your GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET are set."

# Check for essential environment variables
if [ -z "$GOOGLE_OAUTH_CLIENT_ID" ] || [ -z "$GOOGLE_OAUTH_CLIENT_SECRET" ]; then
  echo "Warning: Google OAuth credentials not found in environment."
  echo "Please make sure they are set before logging in."
fi

# Run the Flask application
python run_app.py