#!/usr/bin/env python3
"""
Test script for the price_updater module.
"""
import os
import sys
import json
import logging
from price_updater import fetch_and_store_openrouter_prices, model_prices_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    """Test the price_updater module functionality."""
    print("Testing OpenRouter price updater...")
    
    # Check for API key
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY environment variable not set!")
        return False
    
    print(f"Using API key: {api_key[:5]}...{api_key[-5:]}")
    
    # Fetch prices
    print("Fetching prices from OpenRouter API...")
    success = fetch_and_store_openrouter_prices()
    
    if not success:
        print("ERROR: Failed to fetch prices from OpenRouter API!")
        return False
    
    # Print cached data
    print(f"Successfully fetched prices for {len(model_prices_cache['prices'])} models")
    print(f"Last updated: {model_prices_cache['last_updated']}")
    
    # Print sample data (first 3 models)
    print("\nSample price data (first 3 models):")
    sample_models = list(model_prices_cache['prices'].items())[:3]
    
    for model_id, model_data in sample_models:
        print(f"\nModel: {model_id}")
        print(f"  Model Name: {model_data.get('model_name', 'N/A')}")
        print(f"  Input Price (per million tokens): ${model_data['input_price']:.4f}")
        print(f"  Output Price (per million tokens): ${model_data['output_price']:.4f}")
        print(f"  Context Length: {model_data['context_length']}")
        print(f"  Multimodal: {model_data['is_multimodal']}")
    
    # Check how many zero-cost models are available
    zero_cost_models = [model_id for model_id, data in model_prices_cache['prices'].items() 
                       if data['input_price'] == 0 and data['output_price'] == 0]
    
    print(f"\nZero-cost models available: {len(zero_cost_models)} out of {len(model_prices_cache['prices'])}")
    
    # Sample zero-cost models (up to 3)
    if zero_cost_models:
        print("Sample zero-cost models:")
        for model_id in zero_cost_models[:3]:
            model_data = model_prices_cache['prices'][model_id]
            print(f"  {model_id} ({model_data.get('model_name', 'Unknown')})")
    
    return True

if __name__ == "__main__":
    if main():
        print("\nTest completed successfully!")
    else:
        print("\nTest failed!")
        sys.exit(1)