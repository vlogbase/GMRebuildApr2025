"""
Model Verification Script

This script verifies the availability of models configured in app.py against the OpenRouter API.
It helps identify any models that are no longer available and suggests replacements.
"""
import os
import sys
import json
import logging
import requests
import traceback
from datetime import datetime
from pprint import pformat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('model_verification.log')
    ]
)
logger = logging.getLogger(__name__)

# OpenRouter API URL
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/models'

def get_openrouter_api_key():
    """Get OpenRouter API key from environment variable."""
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        logger.error("OPENROUTER_API_KEY environment variable not set")
        return None
    return api_key

def fetch_available_models():
    """
    Fetch available models from OpenRouter API.
    Returns a list of model IDs.
    """
    api_key = get_openrouter_api_key()
    if not api_key:
        return []
        
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    logger.info("Fetching models from OpenRouter...")
    
    try:
        response = requests.get(
            OPENROUTER_API_URL,
            headers=headers,
            timeout=15.0
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch models: {response.status_code} - {response.text}")
            return []
            
        models_data = response.json()
        available_models = []
        
        for model in models_data.get('data', []):
            model_id = model.get('id')
            model_name = model.get('name')
            is_multimodal = any(keyword in model_id.lower() or keyword in model_name.lower() 
                               for keyword in ['vision', 'image', 'multi', 'gpt-4o'])
            is_free = ':free' in model_id
            
            available_models.append({
                'id': model_id,
                'name': model_name,
                'is_multimodal': is_multimodal,
                'is_free': is_free
            })
            
        # Save to file for reference
        with open('available_models.json', 'w') as f:
            json.dump(available_models, f, indent=2)
            
        logger.info(f"Found {len(available_models)} available models")
        return available_models
        
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        logger.error(traceback.format_exc())
        return []

def load_app_configured_models():
    """
    Load model configurations from app.py.
    This is a simplified approach that assumes certain structures in app.py.
    """
    try:
        # Import these from app.py (must exist in current directory)
        sys.path.append('.')
        from app import (
            OPENROUTER_MODELS,
            DEFAULT_PRESET_MODELS,
            FREE_MODEL_FALLBACKS,
            MULTIMODAL_MODELS,
            SAFE_FALLBACK_MODELS
        )
        
        return {
            'OPENROUTER_MODELS': OPENROUTER_MODELS,
            'DEFAULT_PRESET_MODELS': DEFAULT_PRESET_MODELS,
            'FREE_MODEL_FALLBACKS': FREE_MODEL_FALLBACKS,
            'MULTIMODAL_MODELS': [m for m in MULTIMODAL_MODELS if '/' in m],  # Only include specific model IDs
            'SAFE_FALLBACK_MODELS': SAFE_FALLBACK_MODELS
        }
    except ImportError as e:
        logger.error(f"Failed to import model configurations from app.py: {e}")
        return None

def verify_models(app_models, available_models):
    """
    Verify that models configured in app.py are available in OpenRouter.
    Returns a report of verification results.
    """
    if not app_models or not available_models:
        return "Failed to verify models due to missing data."
        
    available_model_ids = [m['id'] for m in available_models]
    available_model_dict = {m['id']: m for m in available_models}
    
    results = {}
    
    # Check each configuration category
    for category, models in app_models.items():
        if category == 'OPENROUTER_MODELS':
            # This is a dictionary mapping shortnames to full model IDs
            results[category] = {
                'valid': [],
                'invalid': []
            }
            for shortname, model_id in models.items():
                if model_id in available_model_ids:
                    results[category]['valid'].append({
                        'shortname': shortname,
                        'model_id': model_id,
                        'details': available_model_dict.get(model_id)
                    })
                else:
                    results[category]['invalid'].append({
                        'shortname': shortname,
                        'model_id': model_id,
                        'suggested_replacement': find_replacement(model_id, available_models)
                    })
        elif category == 'DEFAULT_PRESET_MODELS':
            # Dictionary mapping preset IDs to model IDs
            results[category] = {
                'valid': [],
                'invalid': []
            }
            for preset_id, model_id in models.items():
                if model_id in available_model_ids:
                    results[category]['valid'].append({
                        'preset_id': preset_id,
                        'model_id': model_id,
                        'details': available_model_dict.get(model_id)
                    })
                else:
                    results[category]['invalid'].append({
                        'preset_id': preset_id,
                        'model_id': model_id,
                        'suggested_replacement': find_replacement(model_id, available_models)
                    })
        else:
            # Lists of model IDs
            results[category] = {
                'valid': [],
                'invalid': []
            }
            for model_id in models:
                if model_id in available_model_ids:
                    results[category]['valid'].append({
                        'model_id': model_id,
                        'details': available_model_dict.get(model_id)
                    })
                else:
                    results[category]['invalid'].append({
                        'model_id': model_id,
                        'suggested_replacement': find_replacement(model_id, available_models)
                    })
                    
    return results

def find_replacement(model_id, available_models):
    """
    Find a suitable replacement for an invalid model ID.
    Uses simple pattern matching to suggest similar models.
    """
    # Extract provider and model name
    parts = model_id.split('/')
    if len(parts) != 2:
        return None
        
    provider, model_name = parts
    
    # Look for models from the same provider first
    provider_models = [m for m in available_models if m['id'].startswith(provider + '/')]
    if provider_models:
        return provider_models[0]['id']
        
    # If model is multimodal, suggest another multimodal model
    if any(keyword in model_id.lower() for keyword in ['vision', 'multi', 'image', 'gpt-4o']):
        multimodal_models = [m for m in available_models if m.get('is_multimodal')]
        if multimodal_models:
            return multimodal_models[0]['id']
            
    # If it was free, suggest another free model
    if ':free' in model_id:
        free_models = [m for m in available_models if m.get('is_free')]
        if free_models:
            return free_models[0]['id']
            
    # Just return the first available model as a fallback
    if available_models:
        return available_models[0]['id']
        
    return None

def generate_report(verification_results):
    """
    Generate a human-readable report from verification results.
    """
    if isinstance(verification_results, str):
        return verification_results
        
    report = []
    report.append(f"MODEL VERIFICATION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    
    for category, results in verification_results.items():
        valid_count = len(results['valid'])
        invalid_count = len(results['invalid'])
        total = valid_count + invalid_count
        
        report.append(f"\n{category} - {valid_count}/{total} Valid ({valid_count/total*100:.1f}%)")
        report.append("-" * 80)
        
        if invalid_count > 0:
            report.append("\nINVALID MODELS:")
            for model in results['invalid']:
                model_id = model.get('model_id')
                replacement = model.get('suggested_replacement')
                
                if 'shortname' in model:
                    report.append(f"  * {model['shortname']} -> {model_id}")
                elif 'preset_id' in model:
                    report.append(f"  * Preset {model['preset_id']} -> {model_id}")
                else:
                    report.append(f"  * {model_id}")
                    
                if replacement:
                    report.append(f"    Suggested replacement: {replacement}")
                else:
                    report.append("    No replacement found")
            
    report.append("\n" + "=" * 80)
    report.append("RECOMMENDATIONS:")
    
    # Count total invalid models
    total_invalid = sum(len(results['invalid']) for results in verification_results.values())
    if total_invalid == 0:
        report.append("✅ All models are valid! No changes needed.")
    else:
        report.append(f"⚠️ Found {total_invalid} invalid models that need to be updated.")
        report.append("Here are suggested replacements to update in app.py:")
        
        for category, results in verification_results.items():
            if len(results['invalid']) > 0:
                report.append(f"\n{category}:")
                
                for model in results['invalid']:
                    if 'shortname' in model:
                        report.append(f'    "{model["shortname"]}": "{model.get("suggested_replacement")}"')
                    elif 'preset_id' in model:
                        report.append(f'    "{model["preset_id"]}": "{model.get("suggested_replacement")}"')
                    else:
                        report.append(f'    "{model.get("suggested_replacement")}"')
    
    return "\n".join(report)

def run_verification():
    """
    Run the full verification process.
    """
    logger.info("Starting model verification...")
    
    # Fetch available models from OpenRouter
    available_models = fetch_available_models()
    if not available_models:
        logger.error("Failed to fetch available models.")
        return
        
    # Load configured models from app.py
    app_models = load_app_configured_models()
    if not app_models:
        logger.error("Failed to load model configurations from app.py.")
        return
        
    # Verify models
    verification_results = verify_models(app_models, available_models)
    
    # Generate report
    report = generate_report(verification_results)
    
    # Save report to file
    with open('model_verification_report.txt', 'w') as f:
        f.write(report)
        
    # Save verification results as JSON
    with open('model_verification_results.json', 'w') as f:
        json.dump(verification_results, f, indent=2)
        
    # Print report to console
    print(report)
    
    logger.info("Model verification completed. Results saved to model_verification_report.txt")

if __name__ == "__main__":
    run_verification()