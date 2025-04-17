#!/bin/bash
# Run the server in the background
python start_server.py &
echo "Server started. Listening on port 5000."
sleep 3  # Wait a bit to let the server initialize