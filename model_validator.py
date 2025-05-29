"""
Model validator module for OpenRouter API integration.

This module provides helper functions to validate model IDs against OpenRouter's available models
and to safely fallback to alternative models when the requested model is not available.
"""
import os
import json
import time
import logging
import requests
import traceback

logger = logging.getLogger(__name__)

def get_available_models():
    """
    Get a list of all available model IDs from the database (primary source)
    or fallback to OpenRouter API if the database is empty.
    
    Returns:
        list: List of model IDs available
    """
    try:
        # First try to get models from database (most reliable source)
        logger.info("🔍 Attempting to fetch models from database")
        try:
            from app import app
            from models import OpenRouterModel
            
            with app.app_context():
                # Only include active models
                db_models = OpenRouterModel.query.filter_by(model_is_active=True).all()
                logger.info(f"🔍 Database query returned {len(db_models) if db_models else 0} active models")
                
                if db_models:
                    model_ids = [model.model_id for model in db_models]
                    logger.info(f"✅ Found {len(model_ids)} models in database")
                    logger.info(f"🔍 Sample model IDs: {model_ids[:10]}")
                    
                    # Still update the cache file for backward compatibility
                    try:
                        with open('available_models.json', 'w') as f:
                            json.dump(model_ids, f, indent=2)
                        logger.info("✅ Updated cache file with database models")
                    except Exception as cache_write_error:
                        logger.warning(f"⚠️ Could not update cache file: {cache_write_error}")
                        
                    return model_ids
                else:
                    logger.warning("❌ No models found in database, will try API")
        except Exception as db_error:
            logger.error(f"❌ Error accessing database models: {db_error}")
            import traceback
            logger.error(f"❌ Database error traceback: {traceback.format_exc()}")
        
        # If database access failed, try direct API call
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            logger.error("OPENROUTER_API_KEY not found")
            return []
            
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        logger.info("Fetching models from OpenRouter API for validation...")
        response = requests.get(
            'https://openrouter.ai/api/v1/models',
            headers=headers,
            timeout=15.0
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch models: {response.status_code} - {response.text}")
            return []
            
        data = response.json()
        models = [model['id'] for model in data.get('data', [])]
        logger.info(f"Found {len(models)} available models via API")
        
        # Cache the results to a file for offline reference
        with open('available_models.json', 'w') as f:
            json.dump(models, f, indent=2)
            
        # Try to update the database with these models for future use
        try:
            from migrations_openrouter_model import fetch_and_populate_models
            fetch_and_populate_models()
            logger.info("Updated database with models from API")
        except Exception as migration_error:
            logger.error(f"Failed to update database with API models: {migration_error}")
            
        return models
    except Exception as e:
        logger.error(f"Error fetching available models: {e}")
        logger.error(traceback.format_exc())
        
        # Try to load from cache if available
        try:
            if os.path.exists('available_models.json'):
                with open('available_models.json', 'r') as f:
                    models = json.load(f)
                logger.info(f"Loaded {len(models)} models from cache file")
                return models
        except Exception as cache_error:
            logger.error(f"Error loading cached models: {cache_error}")
            
        return []

def is_model_available(model_id, available_models=None):
    """
    Check if a model ID is available in OpenRouter.
    
    Args:
        model_id (str): The model ID to check
        available_models (list, optional): List of available models (if already fetched)
        
    Returns:
        bool: True if the model is available, False otherwise
    """
    if available_models is None:
        available_models = get_available_models()
    
    # Enhanced logging for debugging availability issues
    logger.info(f"🔍 Checking availability for model: {model_id}")
    logger.info(f"🔍 Available models count: {len(available_models) if available_models else 0}")
    logger.info(f"🔍 Available models sample (first 10): {available_models[:10] if available_models else 'None'}")
    
    if not available_models:
        logger.error("❌ No available models list - treating all models as unavailable")
        return False
    
    is_available = model_id in available_models
    logger.info(f"🔍 Model {model_id} availability: {is_available}")
    
    if not is_available:
        # Log similar models to help debug typos or version mismatches
        similar_models = [m for m in available_models if model_id.split('/')[-1] in m or m.split('/')[-1] in model_id]
        if similar_models:
            logger.warning(f"❌ Model {model_id} not found, but similar models exist: {similar_models[:5]}")
        else:
            logger.warning(f"❌ Model {model_id} not found and no similar models detected")
        
    return is_available

def get_fallback_model(requested_model, fallback_models, available_models=None):
    """
    Get a fallback model if the requested model is not available.
    
    Args:
        requested_model (str): The original model ID requested
        fallback_models (list): List of fallback model IDs to try
        available_models (list, optional): List of available models (if already fetched)
        
    Returns:
        str: The best available fallback model ID or None if no fallbacks are available
    """
    if available_models is None:
        available_models = get_available_models()
        
    # First check if the requested model is available
    if is_model_available(requested_model, available_models):
        return requested_model
        
    logger.warning(f"Requested model {requested_model} is not available, searching for fallback")
    
    # Check fallback models in order of preference
    for fallback in fallback_models:
        if is_model_available(fallback, available_models):
            logger.info(f"Using fallback model {fallback} instead of {requested_model}")
            return fallback
            
    # If no fallbacks are available, return the first available model (if any)
    if available_models:
        logger.warning(f"No fallback models available, using first available model: {available_models[0]}")
        return available_models[0]
        
    # If no models are available at all, return None
    logger.error("No models are available!")
    return None

def select_multimodal_fallback(has_image_content, available_models=None, has_rag_content=False):
    """
    Select an appropriate model based on content type (images, documents, etc).
    Tries to use database query first for efficiency, then falls back to list filtering.
    
    Args:
        has_image_content (bool): Whether the message contains image content
        available_models (list, optional): List of available models (if already fetched)
        has_rag_content (bool, optional): Whether the message contains RAG document context
        
    Returns:
        str: The best available model ID appropriate for the content type
    """
    try:
        # First try to get models directly from the database by capability
        from app import app
        from models import OpenRouterModel
        
        with app.app_context():
            # Only consider active models
            model_query = OpenRouterModel.query.filter_by(model_is_active=True)
            
            # Filter by capability
            if has_image_content:
                model_query = model_query.filter(OpenRouterModel.is_multimodal == True)
            
            # Add reasoning preference for text or RAG models
            if not has_image_content or has_rag_content:
                # Try to get reasoning models first - these are better for RAG content and complex text
                reasoning_models = model_query.filter(OpenRouterModel.supports_reasoning == True).order_by(
                    OpenRouterModel.output_price_usd_million.desc()).limit(5).all()
                
                if reasoning_models:
                    model_id = reasoning_models[0].model_id
                    logger.info(f"Selected reasoning model from database: {model_id} (RAG content: {has_rag_content})")
                    return model_id
            
            # Get the most powerful models first (assuming higher price = more powerful)
            # For image models, we need multimodal capability
            candidate_models = model_query.order_by(OpenRouterModel.output_price_usd_million.desc()).limit(5).all()
            
            if candidate_models:
                model_id = candidate_models[0].model_id
                logger.info(f"Selected {'multimodal' if has_image_content else 'text'} model from database: {model_id}")
                return model_id
    except Exception as db_error:
        logger.error(f"Error selecting model from database: {db_error}")
    
    # Fallback to list-based selection if database query failed
    if available_models is None:
        available_models = get_available_models()
    
    # Priority list for multimodal models
    multimodal_priority = [
        "anthropic/claude-3-opus-20240229",
        "anthropic/claude-3-sonnet-20240229",
        "anthropic/claude-3-haiku-20240307",
        "openai/gpt-4-vision-preview",
        "openai/gpt-4o-2024-05-13",
        "google/gemini-pro-vision"
    ]
    
    # Priority list for text-only models
    text_priority = [
        "anthropic/claude-3-opus-20240229",
        "anthropic/claude-3-sonnet-20240229",
        "anthropic/claude-3-haiku-20240307",
        "openai/gpt-4o-2024-05-13",
        "openai/gpt-4",
        "google/gemini-pro",
        "meta-llama/llama-3-8b"
    ]
    
    # Priority list for RAG/document content (need models with larger context windows)
    rag_priority = [
        "anthropic/claude-3-opus-20240229",  # Largest context window
        "anthropic/claude-3-sonnet-20240229", # Large context window
        "openai/gpt-4o-2024-05-13",          # Good context and reasoning
        "anthropic/claude-3-haiku-20240307",  # Smaller but still good for RAG
        "openai/gpt-4-turbo-preview",
        "google/gemini-pro"
    ]
    
    # Select the right priority list based on content
    if has_image_content:
        priority_list = multimodal_priority
    elif has_rag_content:
        priority_list = rag_priority
        logger.info("Using RAG-optimized model priority list")
    else:
        priority_list = text_priority
    
    # Check each model in order of priority
    for model_id in priority_list:
        if model_id in available_models:
            logger.info(f"Selected {'multimodal' if has_image_content else 'text-only'} model: {model_id}")
            return model_id
    
    # If no priority models are available, return the first available model (if any)
    if available_models:
        logger.warning(f"No preferred models available, using first available model: {available_models[0]}")
        return available_models[0]
        
    # If no models are available at all, return a hardcoded fallback
    logger.error("No models are available! Using hardcoded fallback: anthropic/claude-3-haiku-20240307")
    return "anthropic/claude-3-haiku-20240307"