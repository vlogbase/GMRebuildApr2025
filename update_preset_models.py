"""
Script to update the DEFAULT_PRESET_MODELS in app.py with valid replacements for outdated models.

This script is designed to be run when OpenRouter has updated or removed models that are
referenced in the DEFAULT_PRESET_MODELS dictionary. It will check each model in the dictionary,
and if it's found to be inactive or unavailable, it will attempt to replace it with an
appropriate alternative.
"""

import os
import logging
import sys
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Model type mapping to help with finding replacements
MODEL_TYPE_MAPPINGS = {
    "claude-3-haiku": ["claude-3-haiku", "claude-3-sonnet", "gemini-pro"],
    "claude-3-sonnet": ["claude-3-sonnet", "claude-3-opus", "gpt-4o"],
    "claude-3-opus": ["claude-3-opus", "gpt-4o", "claude-3-sonnet"],
    "gemini-pro-vision": ["gemini-pro-vision", "gpt-4o", "gpt-4-vision"],
    "gpt-4o": ["gpt-4o", "gpt-4", "claude-3-opus"],
    "llama-3": ["llama-3", "llama-2", "mistral"],
    "gemini-flash": ["gemini-flash", "gemini-flash:free", "claude-instant:free", "gpt-3.5-turbo:free"]
}

def find_replacement_model(model_id, vendor=None, active_models=None):
    """
    Find a suitable replacement for a model that is no longer available.
    
    Args:
        model_id (str): The original model ID that needs replacement
        vendor (str, optional): Preferred vendor (e.g., 'anthropic', 'google')
        active_models (list, optional): List of active models to choose from
        
    Returns:
        str: A suitable replacement model ID
    """
    from app import app
    from models import OpenRouterModel
    
    with app.app_context():
        # Get all active models if not provided
        if active_models is None:
            active_models = OpenRouterModel.query.filter_by(model_is_active=True).all()
            active_models = [m.model_id for m in active_models]
            
        # Check if the original model is still active
        if model_id in active_models:
            logger.info(f"Model {model_id} is still active, no replacement needed")
            return model_id
            
        # Extract the base name (without version)
        model_parts = model_id.split('/')
        if len(model_parts) < 2:
            logger.warning(f"Invalid model format: {model_id}")
            return model_id
            
        model_vendor = model_parts[0]
        model_name = model_parts[1].split(':')[0].split('-20')[0] if '-20' in model_parts[1] else model_parts[1].split(':')[0]
        logger.info(f"Finding replacement for {model_id} (vendor: {model_vendor}, name: {model_name})")
        
        # Try to find a model with the same name but newer version
        same_name_models = [m for m in active_models if 
                           model_name in m.lower() and 
                           (not vendor or m.startswith(f"{vendor}/"))]
        
        if same_name_models:
            logger.info(f"Found models with same name: {same_name_models}")
            # Prefer same vendor if possible
            same_vendor_models = [m for m in same_name_models if m.startswith(f"{model_vendor}/")]
            if same_vendor_models:
                logger.info(f"Selected replacement from same vendor: {same_vendor_models[0]}")
                return same_vendor_models[0]
            
            # Otherwise return first match
            logger.info(f"Selected replacement from different vendor: {same_name_models[0]}")
            return same_name_models[0]
            
        # Try to find a model based on type mapping
        for base_model, alternatives in MODEL_TYPE_MAPPINGS.items():
            if base_model in model_name:
                logger.info(f"Trying alternatives for {base_model}: {alternatives}")
                for alt in alternatives:
                    alt_models = [m for m in active_models if alt in m.lower()]
                    if alt_models:
                        logger.info(f"Selected alternative model: {alt_models[0]}")
                        return alt_models[0]
        
        # If all else fails, return first model in priority vendor order
        priority_vendors = ["anthropic", "openai", "google", "meta-llama", "mistral"]
        for vendor in priority_vendors:
            vendor_models = [m for m in active_models if m.startswith(f"{vendor}/")]
            if vendor_models:
                logger.info(f"Selected fallback from vendor {vendor}: {vendor_models[0]}")
                return vendor_models[0]
                
        # If somehow we have no models at all
        logger.error("No active models found!")
        return model_id  # Return original as last resort

def update_preset_models():
    """
    Check and update the DEFAULT_PRESET_MODELS dictionary in app.py
    with valid replacements for outdated models.
    """
    try:
        from app import app, DEFAULT_PRESET_MODELS
        from models import OpenRouterModel
        
        with app.app_context():
            # Get all active models
            active_models = OpenRouterModel.query.filter_by(model_is_active=True).all()
            active_model_ids = [m.model_id for m in active_models]
            
            if not active_model_ids:
                logger.error("No active models found in database!")
                return False
                
            logger.info(f"Found {len(active_model_ids)} active models")
            
            # Check each model in DEFAULT_PRESET_MODELS and replace if needed
            updated_models = {}
            updates_needed = False
            
            for preset_id, model_id in DEFAULT_PRESET_MODELS.items():
                if model_id not in active_model_ids:
                    logger.warning(f"Preset {preset_id} model {model_id} is inactive or unavailable")
                    replacement = find_replacement_model(model_id, active_models=active_model_ids)
                    updated_models[preset_id] = replacement
                    updates_needed = True
                    logger.info(f"Will replace preset {preset_id}: {model_id} → {replacement}")
                else:
                    updated_models[preset_id] = model_id
                    logger.info(f"Preset {preset_id} model {model_id} is still active")
            
            if not updates_needed:
                logger.info("All preset models are active, no updates needed")
                return True
                
            # Update the app.py file
            with open('app.py', 'r') as f:
                content = f.read()
                
            # Find the DEFAULT_PRESET_MODELS dictionary in the file
            default_models_start = content.find('DEFAULT_PRESET_MODELS = {')
            if default_models_start == -1:
                logger.error("Could not find DEFAULT_PRESET_MODELS in app.py")
                return False
                
            default_models_end = content.find('}', default_models_start)
            if default_models_end == -1:
                logger.error("Could not find end of DEFAULT_PRESET_MODELS in app.py")
                return False
                
            # Build the new dictionary
            new_dict = 'DEFAULT_PRESET_MODELS = {\n'
            for preset_id, model_id in updated_models.items():
                # Try to preserve comments if they exist in the original
                line_start = content.find(f'"{preset_id}":', default_models_start, default_models_end)
                if line_start != -1:
                    line_end = content.find('\n', line_start, default_models_end)
                    line = content[line_start:line_end]
                    
                    # Check if there's a comment
                    comment_start = line.find('#')
                    if comment_start != -1:
                        comment = line[comment_start:]
                        new_dict += f'    "{preset_id}": "{model_id}", {comment}\n'
                    else:
                        new_dict += f'    "{preset_id}": "{model_id}",\n'
                else:
                    new_dict += f'    "{preset_id}": "{model_id}",\n'
                    
            new_dict += '}'
            
            # Replace the dictionary in the file
            new_content = content[:default_models_start] + new_dict + content[default_models_end+1:]
            
            # Write the updated file
            with open('app.py', 'w') as f:
                f.write(new_content)
                
            logger.info("Updated DEFAULT_PRESET_MODELS in app.py successfully")
            return True
            
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = update_preset_models()
    sys.exit(0 if success else 1)