#!/bin/bash

echo "Starting GloriaMundo application using gunicorn.conf.py..."
echo "This will use the port configuration from gunicorn.conf.py (port 3000)"

# Use gunicorn.conf.py for configuration
exec gunicorn -c gunicorn.conf.py main:app