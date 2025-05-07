"""
Test script to diagnose issues with the /save_preference endpoint.

This script simulates different types of requests to the endpoint
to validate the robust JSON parsing and error handling fixes.
"""

import json
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_save_preference():
    """Test the save_preference endpoint with different request formats"""
    base_url = "http://localhost:5000"  # Adjust if needed
    endpoint = f"{base_url}/save_preference"
    
    # Test cases with different request formats
    test_cases = [
        {
            "name": "Standard JSON format",
            "headers": {"Content-Type": "application/json"},
            "data": json.dumps({"preset_id": "1", "model_id": "google/gemini-1.5-pro"}),
        },
        {
            "name": "Content-Type missing",
            "headers": {},  # No Content-Type header
            "data": json.dumps({"preset_id": "1", "model_id": "google/gemini-1.5-pro"}),
        },
        {
            "name": "Wrong Content-Type",
            "headers": {"Content-Type": "text/plain"},  # Incorrect Content-Type
            "data": json.dumps({"preset_id": "1", "model_id": "google/gemini-1.5-pro"}),
        },
        {
            "name": "Missing preset_id",
            "headers": {"Content-Type": "application/json"},
            "data": json.dumps({"model_id": "google/gemini-1.5-pro"}),
        },
        {
            "name": "Missing model_id",
            "headers": {"Content-Type": "application/json"},
            "data": json.dumps({"preset_id": "1"}),
        },
        {
            "name": "Non-numeric preset_id",
            "headers": {"Content-Type": "application/json"},
            "data": json.dumps({"preset_id": "abc", "model_id": "google/gemini-1.5-pro"}),
        },
        {
            "name": "Out of range preset_id (too high)",
            "headers": {"Content-Type": "application/json"},
            "data": json.dumps({"preset_id": "10", "model_id": "google/gemini-1.5-pro"}),
        },
        {
            "name": "Out of range preset_id (too low)",
            "headers": {"Content-Type": "application/json"},
            "data": json.dumps({"preset_id": "0", "model_id": "google/gemini-1.5-pro"}),
        },
        {
            "name": "Empty request body",
            "headers": {"Content-Type": "application/json"},
            "data": "",
        },
        {
            "name": "Malformed JSON",
            "headers": {"Content-Type": "application/json"},
            "data": "{preset_id: 1, model_id: 'google/gemini-1.5-pro'}", # Missing quotes around keys
        }
    ]
    
    # Run test cases
    for i, test_case in enumerate(test_cases):
        print("\n" + "=" * 70)
        print(f"TEST CASE {i+1}: {test_case['name']}")
        print("=" * 70)
        
        try:
            # Make the request
            print(f"\nRequest:")
            print(f"Headers: {test_case['headers']}")
            print(f"Data: {test_case['data']}")
            
            response = requests.post(
                endpoint,
                headers=test_case['headers'],
                data=test_case['data']
            )
            
            # Log the response
            print(f"\nResponse:")
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            # Try to parse response as JSON if possible
            try:
                response_json = response.json()
                print(f"JSON Response: {json.dumps(response_json, indent=2)}")
            except json.JSONDecodeError:
                print(f"Text Response: {response.text}")
                
            # Analyze the response
            if response.status_code == 200:
                print("\nRESULT: Request SUCCEEDED")
            else:
                print(f"\nRESULT: Request FAILED with status {response.status_code}")
                
        except Exception as e:
            print(f"\nERROR: {str(e)}")
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    # Only run this test when the Flask server is running
    print("Starting save_preference endpoint tests...")
    print("Make sure the Flask application is running on http://localhost:5000")
    print("Press Ctrl+C to cancel or any key to continue...")
    
    try:
        input()  # Wait for user confirmation
        test_save_preference()
    except KeyboardInterrupt:
        print("Tests cancelled.")