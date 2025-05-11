"""
One-time Script to Update OpenRouter Model Data

This script manually triggers the price updater to fetch the latest
model data from OpenRouter, including PDF support information.
"""

import os
import logging
import requests
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directly use the OpenRouter API rather than the full app stack
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

def fetch_and_analyze_pdf_models():
    """Directly fetch from OpenRouter API and analyze PDF-capable models"""
    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY not found in environment variables")
        return False
    
    # Define headers for OpenRouter API
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://gloriamundo.com",
        "X-Title": "GloriaMundo Chatbot"
    }
    
    logger.info("Fetching models from OpenRouter API...")
    
    try:
        # Fetch models from OpenRouter API
        response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch models from OpenRouter. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
        
        models_data = response.json().get('data', [])
        if not models_data:
            logger.error("No models found in the API response")
            return False
        
        logger.info(f"Successfully fetched {len(models_data)} models from OpenRouter API")
        
        # Analyze models for PDF support
        pdf_models = []
        for model in models_data:
            model_id = model.get('id', 'unknown')
            architecture = model.get('architecture', {})
            
            # Check for PDF support based on input modalities
            supports_pdf = False
            if architecture:
                input_modalities = architecture.get('input_modalities', [])
                supports_pdf = 'file' in input_modalities
            
            if supports_pdf:
                pdf_models.append({
                    'id': model_id,
                    'name': model.get('name', model_id.split('/')[-1]),
                    'description': model.get('description', '')
                })
        
        # Output the results
        logger.info(f"Found {len(pdf_models)} models with PDF support:")
        for model in pdf_models:
            logger.info(f"- {model['name']} ({model['id']})")
            
        return True
        
    except Exception as e:
        logger.error(f"Error fetching or processing models from OpenRouter: {e}")
        return False

def main():
    """Main function to run the script"""
    logger.info("Starting OpenRouter model data analysis...")
    success = fetch_and_analyze_pdf_models()
    
    if success:
        logger.info("OpenRouter model analysis completed successfully.")
    else:
        logger.error("Failed to analyze models from OpenRouter")

if __name__ == "__main__":
    main()