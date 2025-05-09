#!/bin/bash

# Exit on error
set -e

# Set admin email
export ADMIN_EMAILS="andy@sentigral.com"

echo "Starting GloriaMundo Admin Dashboard on port 3000..."
echo "Admin access restricted to: $ADMIN_EMAILS"

# Start the admin dashboard
python workflows/gm_admin_workflow.py