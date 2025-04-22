#!/bin/bash

echo "===========================================" 
echo "Starting GloriaMundo Chat with Google Auth"
echo "===========================================" 

echo "Checking for required environment variables..."

# Check for required environment variables
if [ -z "$GOOGLE_OAUTH_CLIENT_ID" ]; then
  echo "⚠️  GOOGLE_OAUTH_CLIENT_ID is not set. Google login will not work."
  echo "Please set up Google OAuth credentials."
fi

if [ -z "$GOOGLE_OAUTH_CLIENT_SECRET" ]; then
  echo "⚠️  GOOGLE_OAUTH_CLIENT_SECRET is not set. Google login will not work."
  echo "Please set up Google OAuth credentials."
fi

if [ -z "$DATABASE_URL" ]; then
  echo "⚠️  DATABASE_URL is not set. Database connections will fail."
  echo "Please set up your database connection string."
fi

echo ""
echo "Running database migrations..."
python migrations_google_auth.py

echo ""
echo "Starting Flask application..."
python run_app.py
