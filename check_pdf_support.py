"""
Simple script to check which models support PDF files via the OpenRouter API.
"""

import os
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_pdf_capable_models():
    """Fetch models from OpenRouter API and identify PDF-capable ones"""
    openrouter_api_key = os.environ.get('OPENROUTER_API_KEY')
    if not openrouter_api_key:
        logger.error("OPENROUTER_API_KEY not found in environment variables")
        return []
    
    # Define headers for OpenRouter API
    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "HTTP-Referer": "https://gloriamundo.com",
        "X-Title": "GloriaMundo Chatbot"
    }
    
    logger.info("Fetching models from OpenRouter API...")
    
    try:
        # Fetch models from OpenRouter API
        response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch models from OpenRouter. Status code: {response.status_code}")
            return []
        
        models_data = response.json().get('data', [])
        if not models_data:
            logger.error("No models found in the API response")
            return []
        
        logger.info(f"Successfully fetched {len(models_data)} models from OpenRouter API")
        
        # Extract model IDs with PDF support
        pdf_models = []
        for model in models_data:
            model_id = model.get('id', '')
            name = model.get('name', model_id.split('/')[-1])
            architecture = model.get('architecture', {})
            
            # Check for PDF support
            supports_pdf = False
            if architecture:
                input_modalities = architecture.get('input_modalities', [])
                supports_pdf = 'file' in input_modalities
            
            if supports_pdf:
                pdf_models.append({
                    'id': model_id,
                    'name': name
                })
        
        # Output the results
        logger.info(f"Found {len(pdf_models)} models with PDF support:")
        for model in pdf_models:
            logger.info(f"- {model['name']} ({model['id']})")
        
        # Save to a JSON file for reference
        with open('pdf_capable_models.json', 'w') as f:
            json.dump(pdf_models, f, indent=2)
        logger.info("PDF-capable models saved to pdf_capable_models.json")
        
        return pdf_models
        
    except Exception as e:
        logger.error(f"Error fetching models from OpenRouter: {e}")
        return []

if __name__ == "__main__":
    get_pdf_capable_models()