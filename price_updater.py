"""
Price Updater Module for GloriaMundo Chatbot

This module handles background fetching and caching of OpenRouter model prices.
"""

import os
import time
import logging
import requests
from datetime import datetime

# Set up logging with more details for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialize a cache dict to store model prices
model_prices_cache = {
    'prices': {},
    'last_updated': None
}

def fetch_and_store_openrouter_prices() -> bool:
    """
    Fetch current model prices from OpenRouter API and store them in the cache.
    This function also updates the global OPENROUTER_MODELS_INFO variable
    to ensure consistent model data across the application.
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Mark the start time for performance tracking
    start_time = time.time()
    logger.info("Scheduled job: fetch_and_store_openrouter_prices started")
    
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
        
        # Log the API request details (without exposing the full key)
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        logger.debug(f"API Request URL: https://openrouter.ai/api/v1/models")
        logger.debug(f"Using API key: {masked_key}")
        
        response = requests.get(
            'https://openrouter.ai/api/v1/models',
            headers=headers,
            timeout=15.0
        )
        
        # Log response status
        logger.debug(f"OpenRouter API response status code: {response.status_code}")
        
        # Check response status
        response.raise_for_status()
        
        # Parse response JSON
        models_data = response.json()
        
        # Log response data (limited for brevity)
        data_count = len(models_data.get('data', []))
        logger.debug(f"Received data for {data_count} models from OpenRouter API")
        
        # Process model data to extract pricing
        prices = {}
        markup_factor = 2.0  # Our markup for pricing
        
        # Process models for OPENROUTER_MODELS_INFO and populate it
        processed_models = []
        
        for model in models_data.get('data', []):
            model_id = model.get('id', '')
            
            # Skip if model_id is empty
            if not model_id:
                continue
                
            # Extract pricing information
            pricing = model.get('pricing', {})
            input_price_str = pricing.get('prompt', '0') 
            output_price_str = pricing.get('completion', '0')
            
            # Convert string prices to float, handling any format issues
            try:
                input_price = float(input_price_str) if input_price_str else 0
            except ValueError:
                logger.warning(f"Invalid input price format for {model_id}: {input_price_str}, using 0")
                input_price = 0
                
            try:
                output_price = float(output_price_str) if output_price_str else 0
            except ValueError:
                logger.warning(f"Invalid output price format for {model_id}: {output_price_str}, using 0")
                output_price = 0
            
            # Check if model has multimodal capabilities from architecture
            architecture = model.get('architecture', {})
            is_multimodal = False
            
            if architecture:
                input_modalities = architecture.get('input_modalities', [])
                is_multimodal = len(input_modalities) > 1 or 'image' in input_modalities
            
            # Apply our markup and store in the cache
            # Calculate per million tokens pricing for easier display/calculation
            input_price_million = input_price * 1000000
            output_price_million = output_price * 1000000
            
            # Apply markup
            marked_up_input = input_price_million * markup_factor
            marked_up_output = output_price_million * markup_factor
            
            # Calculate cost band based on the higher of input and output price
            max_price = max(marked_up_input, marked_up_output)
            
            # Determine the cost band
            cost_band = ""
            if max_price >= 100.0:
                cost_band = "$$$$"
            elif max_price >= 10.0:
                cost_band = "$$$"
            elif max_price >= 1.0:
                cost_band = "$$"
            elif max_price >= 0.01:
                cost_band = "$"
            else:
                cost_band = ""  # Free or nearly free models get no cost band
            
            prices[model_id] = {
                'input_price': marked_up_input,  # Price per million tokens with markup
                'output_price': marked_up_output,  # Price per million tokens with markup
                'raw_input_price': input_price_million,  # Price per million tokens without markup
                'raw_output_price': output_price_million,  # Price per million tokens without markup
                'context_length': model.get('context_length', 'Unknown'),
                'is_multimodal': is_multimodal or model.get('is_multimodal', False),
                'model_name': model.get('name', model_id.split('/')[-1]),
                'cost_band': cost_band  # Add cost band indicator
            }
            
            # Also add the specific properties needed for OPENROUTER_MODELS_INFO
            model_name = model.get('name', '').lower()
            model_description = model.get('description', '').lower()
            model_id_lower = model_id.lower()
            
            # Add the classification properties needed by app.py
            model['is_free'] = ':free' in model_id_lower or input_price == 0.0
            model['is_multimodal'] = is_multimodal or any(keyword in model_id_lower or keyword in model_name or keyword in model_description 
                                    for keyword in ['vision', 'image', 'multi', 'gpt-4o'])
            model['is_perplexity'] = 'perplexity/' in model_id_lower
            model['is_reasoning'] = any(keyword in model_id_lower or keyword in model_name or keyword in model_description 
                                    for keyword in ['reasoning', 'opus', 'o1', 'o3'])
            
            # Add to processed models for OPENROUTER_MODELS_INFO
            processed_models.append(model)
        
        # Update the cache with the new prices
        model_prices_cache['prices'] = prices
        model_prices_cache['last_updated'] = datetime.now().isoformat()
        
        # Update the global OPENROUTER_MODELS_INFO in app.py
        try:
            # Import is done here to avoid circular imports
            import app
            app.OPENROUTER_MODELS_INFO = processed_models
            
            # Also update the cache dictionary in app.py
            if hasattr(app, 'OPENROUTER_MODELS_CACHE'):
                app.OPENROUTER_MODELS_CACHE["data"] = {"data": processed_models}
                app.OPENROUTER_MODELS_CACHE["timestamp"] = time.time()
                logger.info(f"Updated OPENROUTER_MODELS_CACHE with {len(processed_models)} models")
            
            logger.info(f"Successfully updated OPENROUTER_MODELS_INFO with {len(processed_models)} models")
        except ImportError as e:
            logger.error(f"Failed to update OPENROUTER_MODELS_INFO: {e}")
        
        # Log successful completion
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully fetched and cached prices for {len(prices)} models in {elapsed_time:.2f} seconds")
        logger.info("Scheduled job: fetch_and_store_openrouter_prices completed successfully")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching model prices: {e}")
        logger.info("Scheduled job: fetch_and_store_openrouter_prices failed")
        return False
    except Exception as e:
        logger.error(f"Error fetching or processing model prices: {e}")
        logger.info("Scheduled job: fetch_and_store_openrouter_prices failed")
        return False

def get_model_cost(model_id: str) -> dict:
    """
    Get the cost per million tokens and cost band for a specific model.
    
    Args:
        model_id (str): The ID of the model
        
    Returns:
        dict: Dictionary containing prompt_cost_per_million, completion_cost_per_million, and cost_band
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
        
        # Define prompt and completion costs with fallback values
        prompt_cost = 0.0
        completion_cost = 0.0
        
        if "gpt-4" in model_name:
            prompt_cost = 60.0
            completion_cost = 120.0
            cost_band = "$$$$"
        elif "claude-3" in model_name and "opus" in model_name:
            prompt_cost = 45.0
            completion_cost = 90.0
            cost_band = "$$$$"
        elif "claude-3" in model_name and "sonnet" in model_name:
            prompt_cost = 15.0
            completion_cost = 30.0
            cost_band = "$$$"
        elif "claude-3" in model_name and "haiku" in model_name:
            prompt_cost = 3.0
            completion_cost = 6.0
            cost_band = "$$"
        elif "gemini-1.5" in model_name and "pro" in model_name:
            prompt_cost = 10.0
            completion_cost = 20.0
            cost_band = "$$$"
        elif "gpt-3.5" in model_name:
            prompt_cost = 1.0
            completion_cost = 2.0
            cost_band = "$$"
        else:
            # Default fallback for unknown models
            prompt_cost = 10.0
            completion_cost = 20.0
            cost_band = "$$$"
            
        # Return the fallback data with cost band
        return {
            'prompt_cost_per_million': prompt_cost,
            'completion_cost_per_million': completion_cost,
            'cost_band': cost_band
        }
    
    # Prices are already stored per million tokens
    return {
        'prompt_cost_per_million': model_data['input_price'],
        'completion_cost_per_million': model_data['output_price'],
        'cost_band': model_data.get('cost_band', '')
    }