#!/bin/bash

echo "Starting GloriaMundo application on port 3000..."

# Use gunicorn with configuration file for consistent port settings
gunicorn -c gunicorn.conf.py main:app