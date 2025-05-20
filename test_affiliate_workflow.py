"""
Simple script to run the test affiliate template in the Replit environment.
"""

import os
import logging
from test_affiliate_tabs import app

def run():
    """
    Run the test application.
    """
    try:
        # Start the Flask server on port 5000
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logging.error(f"Error running test affiliate app: {e}")
        raise

if __name__ == "__main__":
    run()