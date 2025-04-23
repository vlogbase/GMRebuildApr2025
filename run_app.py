#!/usr/bin/env python3
"""
Start script for the Flask application.
This script ensures that the correct environment variables are set,
and starts the application with pre-loaded price data.
"""
import os
import sys
import logging
from price_updater import fetch_and_store_openrouter_prices

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

if __name__ == "__main__":
    # Set up Flask environment
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'development'
    
    # Pre-load price data from OpenRouter before starting the app
    logging.info("Pre-fetching model prices from OpenRouter API...")
    success = fetch_and_store_openrouter_prices()
    
    if success:
        logging.info("Successfully pre-fetched model pricing data")
    else:
        logging.warning("Failed to pre-fetch model pricing data. Will try again when the app starts.")
    
    # Now import the app
    from app import app
    
    # Run the Flask app
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port)