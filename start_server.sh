#!/bin/bash
# This script starts the Flask server using Gunicorn with Gevent workers

# Apply any database migrations
python migrations_image_url.py

# Start the server
exec gunicorn main:app -k gevent -w 4 --timeout 300 --bind 0.0.0.0:5000 --reload