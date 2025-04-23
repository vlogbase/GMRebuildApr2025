"""
Price Updater Module for GloriaMundo Chatbot

This module handles background fetching and caching of OpenRouter model prices.
"""

import os
import time
import logging
import requests
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# Initialize a cache dict to store model prices
model_prices_cache = {
    'prices': {},
    'last_updated': None
}

def fetch_and_store_openrouter_prices() -> bool:
    """
    Fetch current model prices from OpenRouter API and store them in the cache.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            logger.error("OPENROUTER_API_KEY not found in environment variables")
            return False

        # Define headers for OpenRouter API
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Fetch models from OpenRouter
        logger.info("Fetching model prices from OpenRouter API...")
        response = requests.get(
            'https://openrouter.ai/api/v1/models',
            headers=headers,
            timeout=15.0
        )
        
        # Check response status
        response.raise_for_status()
        models_data = response.json()
        
        # Process model data to extract pricing
        prices = {}
        markup_factor = 2.0  # Our markup for pricing
        
        for model in models_data.get('data', []):
            model_id = model.get('id', '')
            
            # Skip if model_id is empty
            if not model_id:
                continue
                
            # Extract pricing information
            pricing = model.get('pricing', {})
            input_price = pricing.get('prompt', 0)
            output_price = pricing.get('completion', 0)
            
            # Apply our markup and store in the cache
            prices[model_id] = {
                'input_price': float(input_price) * markup_factor if input_price else 0,
                'output_price': float(output_price) * markup_factor if output_price else 0,
                'raw_input_price': float(input_price) if input_price else 0,
                'raw_output_price': float(output_price) if output_price else 0,
                'context_length': model.get('context_length', 'Unknown'),
                'is_multimodal': model.get('is_multimodal', False)
            }
        
        # Update the cache with the new prices
        model_prices_cache['prices'] = prices
        model_prices_cache['last_updated'] = datetime.now().isoformat()
        
        logger.info(f"Successfully fetched and cached prices for {len(prices)} models")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching model prices: {e}")
        return False
    except Exception as e:
        logger.error(f"Error fetching or processing model prices: {e}")
        return False

def get_model_cost(model_id: str) -> dict:
    """
    Get the cost per million tokens for a specific model.
    
    Args:
        model_id (str): The ID of the model
        
    Returns:
        dict: Dictionary containing prompt_cost_per_million and completion_cost_per_million
    """
    # If the cache is empty, try to fetch prices
    if not model_prices_cache['prices']:
        fetch_and_store_openrouter_prices()
    
    # Get the model data from the cache
    model_data = model_prices_cache['prices'].get(model_id, {})
    
    # If we don't have data for this specific model, use fallback logic
    if not model_data:
        # Approximate fallback costs based on model name
        model_name = model_id.lower()
        
        if "gpt-4" in model_name:
            return {'prompt_cost_per_million': 60.0, 'completion_cost_per_million': 120.0}
        elif "claude-3" in model_name and "opus" in model_name:
            return {'prompt_cost_per_million': 45.0, 'completion_cost_per_million': 90.0}
        elif "claude-3" in model_name and "sonnet" in model_name:
            return {'prompt_cost_per_million': 15.0, 'completion_cost_per_million': 30.0}
        elif "claude-3" in model_name and "haiku" in model_name:
            return {'prompt_cost_per_million': 3.0, 'completion_cost_per_million': 6.0}
        elif "gemini-1.5" in model_name and "pro" in model_name:
            return {'prompt_cost_per_million': 10.0, 'completion_cost_per_million': 20.0}
        elif "gpt-3.5" in model_name:
            return {'prompt_cost_per_million': 1.0, 'completion_cost_per_million': 2.0}
        else:
            # Default fallback for unknown models
            return {'prompt_cost_per_million': 10.0, 'completion_cost_per_million': 20.0}
    
    # Convert to price per million tokens for easier calculation
    input_price_per_million = model_data['input_price'] * 1000000
    output_price_per_million = model_data['output_price'] * 1000000
    
    return {
        'prompt_cost_per_million': input_price_per_million,
        'completion_cost_per_million': output_price_per_million
    }