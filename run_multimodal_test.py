"""
Script to run the multimodal test with a generated test image URL.
This automatically runs mini_test.py first to get a valid image URL.
"""
import os
import re
import json
import subprocess
import sys

def main():
    print("Running mini_test.py to generate a test image...")
    try:
        # Run the mini_test.py script and capture its output
        result = subprocess.run(['python', 'mini_test.py'], capture_output=True, text=True)
        
        # Check if mini_test was successful
        if result.returncode != 0:
            print(f"Error running mini_test.py: {result.stderr}")
            return
        
        # Parse the output to find the image URL
        output = result.stdout
        
        # Look for the image URL pattern in the output
        url_match = re.search(r'Image URL: (https://[\S]+)', output)
        if not url_match:
            print("Could not find image URL in mini_test.py output")
            print("OUTPUT:", output)
            return
        
        # Extract the image URL
        image_url = url_match.group(1)
        print(f"Found image URL: {image_url}")
        
        # Set the environment variable for the test script
        os.environ['TEST_IMAGE_URL'] = image_url
        
        # Run the multimodal test script
        print("\nRunning test_openrouter_multimodal.py with the generated image URL...")
        subprocess.run(['python', 'test_openrouter_multimodal.py'])
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()