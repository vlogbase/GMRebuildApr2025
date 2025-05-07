"""
Price Updater Module for GloriaMundo Chatbot

This module handles background fetching and caching of OpenRouter model prices,
ensuring model information is stored in the database for reliability.
"""

import os
import time
import logging
import requests
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

# Set up logging with more details for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialize a cache dict to store model prices (kept for backward compatibility)
model_prices_cache = {
    'prices': {},
    'last_updated': None
}

def fetch_and_store_openrouter_prices() -> bool:
    """
    Fetch current model prices from OpenRouter API and store them in the database.
    
    This function now:
    1. Fetches models from the OpenRouter API
    2. Stores them in the database using the OpenRouterModel model
    3. Also updates the legacy cache for backward compatibility
    4. Updates the global OPENROUTER_MODELS_INFO variable for consistency
    
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
        
        # Update the cache with the new prices (kept for backward compatibility)
        model_prices_cache['prices'] = prices
        model_prices_cache['last_updated'] = datetime.now().isoformat()
        
        # Store models in the database (This is the new primary storage method)
        try:
            # Import here to avoid circular imports
            from app import db
            from models import OpenRouterModel
            
            updated_count = 0
            new_count = 0
            
            # Use a single database session for all operations
            for model_id, model_data in prices.items():
                try:
                    # Try to get existing model from the database
                    db_model = db.session.get(OpenRouterModel, model_id)
                    
                    if db_model:
                        # Update existing model
                        db_model.name = model_data['model_name']
                        
                        # Find the original model object to get description
                        original_model = next((m for m in models_data.get('data', []) if m.get('id') == model_id), {})
                        db_model.description = original_model.get('description', '')
                        
                        # Update pricing and other details
                        db_model.context_length = model_data['context_length'] if isinstance(model_data['context_length'], int) else None
                        db_model.input_price_usd_million = model_data['input_price']
                        db_model.output_price_usd_million = model_data['output_price']
                        db_model.is_multimodal = model_data['is_multimodal']
                        db_model.cost_band = model_data['cost_band']
                        
                        # Update additional fields
                        # Check for free models based on price or special tags
                        db_model.is_free = model_data['input_price'] < 0.01 or ':free' in model_id.lower()
                        
                        # Check for reasoning support based on model ID and description
                        model_name = original_model.get('name', '').lower()
                        model_description = original_model.get('description', '').lower()
                        db_model.supports_reasoning = any(keyword in model_id.lower() or keyword in model_name or keyword in model_description 
                                                     for keyword in ['reasoning', 'opus', 'o1', 'o3', 'gpt-4', 'claude-3'])
                        
                        # Update timestamps
                        db_model.last_fetched_at = datetime.utcnow()
                        db_model.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        # Create new model
                        original_model = next((m for m in models_data.get('data', []) if m.get('id') == model_id), {})
                        context_length = model_data['context_length']
                        if not isinstance(context_length, int):
                            try:
                                context_length = int(context_length)
                            except (ValueError, TypeError):
                                context_length = None
                        
                        # Check for free models based on price or special tags
                        is_free = model_data['input_price'] < 0.01 or ':free' in model_id.lower()
                        
                        # Check for reasoning support based on model ID and description
                        model_name = original_model.get('name', '').lower()
                        model_description = original_model.get('description', '').lower()
                        supports_reasoning = any(keyword in model_id.lower() or keyword in model_name or keyword in model_description 
                                            for keyword in ['reasoning', 'opus', 'o1', 'o3', 'gpt-4', 'claude-3'])
                        
                        new_model = OpenRouterModel(
                            model_id=model_id,
                            name=model_data['model_name'],
                            description=original_model.get('description', ''),
                            context_length=context_length,
                            input_price_usd_million=model_data['input_price'],
                            output_price_usd_million=model_data['output_price'],
                            is_multimodal=model_data['is_multimodal'],
                            is_free=is_free,
                            supports_reasoning=supports_reasoning,
                            cost_band=model_data['cost_band'],
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                            last_fetched_at=datetime.utcnow()
                        )
                        db.session.add(new_model)
                        new_count += 1
                        
                except Exception as model_error:
                    logger.error(f"Error updating model {model_id} in database: {model_error}")
                    continue
            
            # Commit all changes in one transaction
            db.session.commit()
            logger.info(f"Database updated: {updated_count} models updated, {new_count} new models added")
            
        except ImportError as e:
            logger.error(f"Failed to import database modules: {e}")
        except SQLAlchemyError as e:
            logger.error(f"Database error storing models: {e}")
            db.session.rollback()
        except Exception as e:
            logger.error(f"Unexpected error storing models in database: {e}")
            if 'db' in locals():
                db.session.rollback()
                
        # Database is now the single source of truth, no need to update global caches
        
        # Log successful completion
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully processed {len(prices)} models in {elapsed_time:.2f} seconds")
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
    This function now primarily uses the database but falls back to cache and then to defaults.
    
    Args:
        model_id (str): The ID of the model
        
    Returns:
        dict: Dictionary containing prompt_cost_per_million, completion_cost_per_million, and cost_band
    """
    try:
        # Try to get model info from the database first (most reliable)
        from models import OpenRouterModel
        
        db_model = OpenRouterModel.query.get(model_id)
        if db_model:
            return {
                'prompt_cost_per_million': db_model.input_price_usd_million,
                'completion_cost_per_million': db_model.output_price_usd_million,
                'cost_band': db_model.cost_band or '',
                'source': 'database'  # For debugging
            }
    except Exception as db_error:
        logger.warning(f"Failed to get model cost from database: {db_error}")
    
    # If database lookup failed, try to fetch fresh data from API
    try:
        # Attempt to update the database with fresh data from the API
        fetch_and_store_openrouter_prices()
        
        # Try database lookup again after the fresh fetch
        db_model = OpenRouterModel.query.get(model_id)
        if db_model:
            return {
                'prompt_cost_per_million': db_model.input_price_usd_million,
                'completion_cost_per_million': db_model.output_price_usd_million,
                'cost_band': db_model.cost_band or '',
                'source': 'database_refresh'  # For debugging
            }
    except Exception as refresh_error:
        logger.warning(f"Failed to refresh model data from API: {refresh_error}")
    
    # If we still don't have data, use fallback logic
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
        'cost_band': cost_band,
        'source': 'fallback'  # For debugging
    }