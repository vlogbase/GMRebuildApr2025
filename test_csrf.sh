#!/bin/bash

# Test script to verify CSRF token handling
echo "Starting CSRF token verification test..."

# Get a CSRF token from the page
echo "Fetching CSRF token from the main page..."
CSRF_TOKEN=$(curl -s -c cookies.txt http://localhost:5000/ | grep -o 'content="[^"]*" name="csrf_token"' | cut -d'"' -f2)

if [ -z "$CSRF_TOKEN" ]; then
    echo "Failed to get CSRF token from the page"
    exit 1
else
    echo "Successfully obtained CSRF token: $CSRF_TOKEN"
fi

# Test a POST request with the CSRF token
echo "Testing POST request to /save_preference with CSRF token..."
RESPONSE=$(curl -s -b cookies.txt -X POST \
    -H "Content-Type: application/json" \
    -H "X-CSRFToken: $CSRF_TOKEN" \
    -d '{"preset_id": "test", "model_id": "test"}' \
    http://localhost:5000/save_preference)

# Display the response
echo "Server response: $RESPONSE"

# Checking if the response indicates a success or authentication issue rather than a CSRF error
if [[ "$RESPONSE" == *"error"* && "$RESPONSE" == *"CSRF"* ]]; then
    echo "CSRF validation failed - token may not be working correctly"
    exit 1
elif [[ "$RESPONSE" == *"error"* && "$RESPONSE" == *"authentication"* ]]; then
    echo "Authentication required - this is expected if not logged in"
    echo "CSRF token handling is working correctly!"
    exit 0
elif [[ "$RESPONSE" == *"success"* ]]; then
    echo "CSRF token handling is working correctly!"
    exit 0
else
    echo "Unexpected response - may need further investigation"
    exit 1
fi