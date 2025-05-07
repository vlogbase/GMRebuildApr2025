#!/usr/bin/env python3
"""
Test script for the /api/refresh_model_prices endpoint.
This script will setup a simple Flask route to test the refresh function.
"""
import os
import sys
import json
import logging
import requests
from flask import Flask, jsonify
from price_updater import fetch_and_store_openrouter_prices, model_prices_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Create a mini Flask app for testing
app = Flask(__name__)

@app.route('/api/refresh_model_prices', methods=['GET', 'POST'])
def refresh_model_prices():
    """Endpoint to refresh model prices from OpenRouter API"""
    try:
        # Call the function to fetch and store prices
        success = fetch_and_store_openrouter_prices()
        
        if success:
            # Count zero-cost models
            zero_cost_models = [model_id for model_id, data in model_prices_cache['prices'].items() 
                              if data['input_price'] == 0 and data['output_price'] == 0]
            
            return jsonify({
                'success': True,
                'prices': model_prices_cache['prices'],
                'last_updated': model_prices_cache['last_updated'],
                'message': f'Model prices refreshed successfully. Found {len(model_prices_cache["prices"])} models, {len(zero_cost_models)} are free.'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to refresh model prices from OpenRouter API'
            })
            
    except Exception as e:
        logging.error(f"Error refreshing model prices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def main():
    """Start the test server"""
    print("Starting test server for refresh endpoint...")
    app.run(host="0.0.0.0", port=5001, debug=True)

if __name__ == "__main__":
    main()