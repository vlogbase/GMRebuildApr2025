#!/usr/bin/env python3
"""
Test script for the price_updater module.
This script tests the functionality of fetching and caching model prices from OpenRouter.
"""
import os
import sys
import json
import logging
from datetime import datetime
from price_updater import fetch_and_store_openrouter_prices, model_prices_cache, get_model_cost

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_price_fetching():
    """Test fetching and caching model prices from OpenRouter."""
    logger.info("Testing price fetching from OpenRouter API...")
    
    # Check that the API key is set
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        logger.error("OPENROUTER_API_KEY environment variable is not set")
        return False
    
    # Fetch prices
    success = fetch_and_store_openrouter_prices()
    
    if not success:
        logger.error("Failed to fetch prices from OpenRouter API")
        return False
    
    # Check that the cache is populated
    if not model_prices_cache['prices']:
        logger.error("Model prices cache is empty after fetch")
        return False
    
    # Print some information about the cached prices
    logger.info(f"Successfully fetched prices for {len(model_prices_cache['prices'])} models")
    logger.info(f"Last updated: {model_prices_cache['last_updated']}")
    
    # Print details for a few popular models
    popular_models = [
        "anthropic/claude-3-opus",
        "anthropic/claude-3-sonnet",
        "anthropic/claude-3-haiku",
        "openai/gpt-4",
        "openai/gpt-4-turbo",
        "openai/gpt-3.5-turbo",
        "google/gemini-1.5-pro"
    ]
    
    logger.info("\nModel pricing details:")
    for model_id in popular_models:
        model_data = model_prices_cache['prices'].get(model_id, {})
        if model_data:
            costs = get_model_cost(model_id)
            logger.info(f"{model_id}:")
            logger.info(f"  Input price (per 1M tokens): ${costs['prompt_cost_per_million']:.2f}")
            logger.info(f"  Output price (per 1M tokens): ${costs['completion_cost_per_million']:.2f}")
        else:
            logger.warning(f"{model_id} not found in cache")
    
    return True

def run_tests():
    """Run all tests."""
    logger.info("Starting price_updater tests...")
    test_price_fetching()
    logger.info("Tests completed")

if __name__ == "__main__":
    run_tests()