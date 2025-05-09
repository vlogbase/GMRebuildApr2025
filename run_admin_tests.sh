#!/bin/bash

# Exit on error
set -e

# Set admin email
export ADMIN_EMAILS="andy@sentigral.com"

echo "Running GloriaMundo Admin Dashboard tests..."
echo "Admin access restricted to: $ADMIN_EMAILS"

# Run the test script
python gm_admin_test.py