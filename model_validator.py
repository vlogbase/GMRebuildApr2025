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
    Get a list of all available model IDs from OpenRouter.
    
    Returns:
        list: List of model IDs available in OpenRouter API
    """
    try:
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            logger.error("OPENROUTER_API_KEY not found")
            return []
            
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        logger.info("Fetching models from OpenRouter for validation...")
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
        logger.info(f"Found {len(models)} available models")
        
        # Cache the results to a file for offline reference
        with open('available_models.json', 'w') as f:
            json.dump(models, f, indent=2)
            
        return models
    except Exception as e:
        logger.error(f"Error fetching available models: {e}")
        logger.error(traceback.format_exc())
        
        # Try to load from cache if available
        try:
            if os.path.exists('available_models.json'):
                with open('available_models.json', 'r') as f:
                    models = json.load(f)
                logger.info(f"Loaded {len(models)} models from cache")
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
        
    return model_id in available_models

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

def select_multimodal_fallback(has_image_content, available_models=None):
    """
    Select an appropriate multimodal fallback model for image content.
    
    Args:
        has_image_content (bool): Whether the message contains image content
        available_models (list, optional): List of available models (if already fetched)
        
    Returns:
        str: The best available multimodal model ID or text model if no multimodal models are available
    """
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
    
    priority_list = multimodal_priority if has_image_content else text_priority
    
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