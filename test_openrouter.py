"""
Test script to verify OpenRouter API connectivity and model fetch capabilities.
This script directly tests the API without going through the Flask application.
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_openrouter_api():
    """Test direct connectivity to OpenRouter API"""
    logger.info("Testing OpenRouter API connectivity...")
    
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        logger.error("OPENROUTER_API_KEY environment variable not found")
        return False
    
    # Only show first and last 2 characters of API key in logs
    masked_key = f"{api_key[:2]}...{api_key[-4:]}"
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
        
        logger.info(f"OpenRouter API response status code: {response.status_code}")
        
        # Check response status
        response.raise_for_status()
        
        # Parse response JSON
        models_data = response.json()
        
        model_count = len(models_data.get('data', []))
        logger.info(f"Successfully fetched {model_count} models from OpenRouter API")
        
        # Save the first 5 models for demonstration
        if model_count > 0:
            logger.info("Sample models from API call:")
            for i, model in enumerate(models_data.get('data', [])[:5]):
                logger.info(f"  {i+1}. {model.get('id')} - {model.get('name')}")
                
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
                
                model_prices[model_id] = {
                    'input_price': input_price_per_token,
                    'output_price': output_price_per_token,
                    'context_window': context_window,
                    'name': model.get('name', model_id)
                }
            
            # Save to file for debugging
            with open('openrouter_models.json', 'w') as f:
                json.dump({
                    'models': model_prices,
                    'timestamp': datetime.now().isoformat(),
                    'count': len(model_prices)
                }, f, indent=2)
            
            logger.info(f"Saved {len(model_prices)} models to openrouter_models.json")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing OpenRouter API: {e}")
        return False

def test_chat_completion_api():
    """Test chat completion API with a simple request"""
    logger.info("\nTesting OpenRouter chat completion API...")
    
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        logger.error("OPENROUTER_API_KEY environment variable not found")
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            # Add HTTP-referer and X-Title headers to prevent certain errors
            'HTTP-Referer': 'https://replit.com/',
            'X-Title': 'OpenRouter Test'
        }
        
        # Sample chat completion request
        data = {
            'model': 'google/gemini-2.5-pro-preview',  # Using a well-known model
            'messages': [
                {'role': 'user', 'content': 'Hello, what is the capital of France?'}
            ]
        }
        
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30.0
        )
        
        logger.info(f"Chat completion response status code: {response.status_code}")
        
        # Check response status
        response.raise_for_status()
        
        # Parse response JSON
        completion_data = response.json()
        
        # Extract and display the response
        if 'choices' in completion_data and len(completion_data['choices']) > 0:
            content = completion_data['choices'][0].get('message', {}).get('content', '')
            logger.info(f"Response content: {content[:200]}...")  # Show first 200 chars
            
            # Log usage information
            usage = completion_data.get('usage', {})
            logger.info(f"Prompt tokens: {usage.get('prompt_tokens', 0)}")
            logger.info(f"Completion tokens: {usage.get('completion_tokens', 0)}")
            logger.info(f"Total tokens: {usage.get('total_tokens', 0)}")
            
            return True
        else:
            logger.error("No choices found in response")
            return False
    
    except Exception as e:
        logger.error(f"Error testing chat completion API: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== Starting OpenRouter API Tests ===")
    
    # Test basic API connectivity
    api_status = test_openrouter_api()
    logger.info(f"\nAPI connectivity test {'PASSED' if api_status else 'FAILED'}")
    
    # Test chat completion API if basic connectivity test passed
    if api_status:
        chat_status = test_chat_completion_api()
        logger.info(f"\nChat completion test {'PASSED' if chat_status else 'FAILED'}")
    
    # Report overall status
    if api_status:
        logger.info("\n==== API TESTS SUCCESSFUL ====")
        logger.info("OpenRouter API is accessible and returning model data correctly")
    else:
        logger.error("\n==== API TESTS FAILED ====")
        logger.error("Please check API key and network connectivity")