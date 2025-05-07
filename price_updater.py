"""
Module to maintain a persistent cache of OpenRouter model prices.

This module uses a singleton pattern and disk persistence to ensure that:
1. The cache is shared between all imports
2. The cache survives application restarts
3. Updates to the cache are immediately visible to all parts of the application
"""

import os
import json
import time
import logging
import pickle
import requests
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelPricesCache:
    """
    Singleton class to maintain a persistent cache of OpenRouter model prices.
    
    This ensures that:
    1. All imports share the same cache
    2. The cache persists across application restarts
    3. Updates are visible to all parts of the application
    
    Example usage:
        from price_updater import model_prices_cache
        
        # Get current prices
        prices = model_prices_cache.get('prices', {})
        
        # Check when prices were last updated
        last_updated = model_prices_cache.get('last_updated')
    """
    
    _instance = None
    _initialized = False
    _data = {
        'prices': {},
        'last_updated': None
    }
    _cache_file = 'openrouter_prices.pkl'
    
    def __new__(cls):
        """Ensure singleton pattern"""
        if cls._instance is None:
            cls._instance = super(ModelPricesCache, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the cache, loading from disk if available"""
        if not self._initialized:
            self._load_cache()
            self._initialized = True
    
    def get(self, key, default=None):
        """Get a value from the cache"""
        return self._data.get(key, default)
    
    def set(self, key, value):
        """Set a value in the cache and persist to disk"""
        self._data[key] = value
        self._save_cache()
    
    def update(self, data):
        """Update multiple values in the cache and persist to disk"""
        self._data.update(data)
        self._save_cache()
    
    def _load_cache(self):
        """Load the cache from disk"""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'rb') as f:
                    self._data = pickle.load(f)
                logger.info(f"Loaded cache from disk with {len(self._data.get('prices', {}))} models")
        except Exception as e:
            logger.error(f"Error loading cache from disk: {e}")
    
    def _save_cache(self):
        """Save the cache to disk"""
        try:
            with open(self._cache_file, 'wb') as f:
                pickle.dump(self._data, f)
            logger.info(f"Saved cache to disk with {len(self._data.get('prices', {}))} models")
        except Exception as e:
            logger.error(f"Error saving cache to disk: {e}")

# Create the singleton instance
model_prices_cache = ModelPricesCache()

def fetch_and_store_openrouter_prices() -> bool:
    """
    Fetch model prices from OpenRouter API and store them in the cache.
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Fetching model prices from OpenRouter API...")
    
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        logger.error("OPENROUTER_API_KEY environment variable not found")
        return False
    
    # Only show first and last 2 characters of API key in logs
    masked_key = f"{api_key[:2]}...{api_key[-4:]}"
    logger.debug(f"API Request URL: https://openrouter.ai/api/v1/models")
    logger.debug(f"Using API key: {masked_key}")
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            'https://openrouter.ai/api/v1/models',
            headers=headers,
            timeout=15.0
        )
        
        logger.debug(f"OpenRouter API response status code: {response.status_code}")
        
        # Check response status
        response.raise_for_status()
        
        # Parse response JSON
        models_data = response.json()
        
        model_count = len(models_data.get('data', []))
        logger.debug(f"Received data for {model_count} models from OpenRouter API")
        
        if model_count == 0:
            logger.error("No models found in API response")
            return False
        
        # Extract pricing information
        model_prices = {}
        
        for model in models_data.get('data', []):
            model_id = model.get('id')
            if not model_id:
                continue
            
            # Get pricing information
            context_window = model.get('context_length', 4000)
            pricing = model.get('pricing', {})
            
            # Default values if pricing information is not available
            input_price_per_token = pricing.get('prompt', 0) 
            output_price_per_token = pricing.get('completion', 0)
            
            # Convert from price per million tokens to price per token
            if input_price_per_token:
                input_price_per_token = input_price_per_token / 1000000
            
            if output_price_per_token:
                output_price_per_token = output_price_per_token / 1000000
            
            model_prices[model_id] = {
                'input_price': input_price_per_token * 1000000,  # Store as price per million tokens
                'output_price': output_price_per_token * 1000000,  # Store as price per million tokens
                'context_window': context_window,
                'name': model.get('name', model_id),
                'description': model.get('description', '')
            }
        
        # Update the cache
        model_prices_cache.update({
            'prices': model_prices,
            'last_updated': datetime.now().isoformat()
        })
        
        logger.info(f"Successfully fetched and cached prices for {len(model_prices)} models")
        return True
    
    except Exception as e:
        logger.error(f"Error fetching model prices from OpenRouter API: {e}")
        return False

# Fetch and store prices if the cache is empty
if not model_prices_cache.get('prices'):
    fetch_and_store_openrouter_prices()