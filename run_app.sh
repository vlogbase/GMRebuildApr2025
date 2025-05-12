#!/bin/bash

# Set up environment
export FLASK_APP=app.py
export FLASK_DEBUG=1

# Run the Flask application using our wrapper script
echo "Starting Flask application..."
python app_workflow.py