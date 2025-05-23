"""
Model Change Monitor
Automatically detects changes in OpenRouter's model list and triggers updates
"""

import requests
import hashlib
import json
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ModelChangeMonitor:
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTER_API_KEY')
        self.last_hash = None
        self.last_check = None
        
    def get_models_hash(self):
        """Get a hash of the current models list from OpenRouter"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'HTTP-Referer': 'https://gloriamundo.sentigral.com',
                'X-Title': 'GloriaMundo AI Chat'
            }
            
            response = requests.get('https://openrouter.ai/api/v1/models', headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            models = data.get('data', [])
            
            # Create a hash based on model IDs, names, and key properties
            model_signature = []
            for model in models:
                signature = {
                    'id': model.get('id'),
                    'name': model.get('name'),
                    'pricing': model.get('pricing', {}),
                    'architecture': model.get('architecture', {}),
                    'supported_parameters': model.get('supported_parameters', [])
                }
                model_signature.append(signature)
            
            # Sort for consistent hashing
            model_signature.sort(key=lambda x: x['id'])
            
            # Create hash
            signature_str = json.dumps(model_signature, sort_keys=True)
            return hashlib.sha256(signature_str.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"Error getting models hash: {e}")
            return None
    
    def check_for_changes(self):
        """Check if the models list has changed"""
        current_hash = self.get_models_hash()
        
        if current_hash is None:
            return False, "Failed to get current models"
        
        if self.last_hash is None:
            # First run - store current hash
            self.last_hash = current_hash
            self.last_check = datetime.utcnow()
            return False, "Initial hash stored"
        
        if current_hash != self.last_hash:
            # Changes detected!
            old_hash = self.last_hash
            self.last_hash = current_hash
            self.last_check = datetime.utcnow()
            return True, f"Changes detected (hash changed from {old_hash[:8]}... to {current_hash[:8]}...)"
        
        # No changes
        self.last_check = datetime.utcnow()
        return False, "No changes detected"
    
    def trigger_update(self):
        """Trigger a full model update when changes are detected"""
        try:
            from price_updater import fetch_and_store_openrouter_prices
            from app import app
            
            with app.app_context():
                logger.info("Triggering model update due to detected changes...")
                success = fetch_and_store_openrouter_prices(force_update=True)
                
                if success:
                    logger.info("Model update completed successfully")
                    return True, "Update completed"
                else:
                    logger.error("Model update failed")
                    return False, "Update failed"
                    
        except Exception as e:
            logger.error(f"Error triggering update: {e}")
            return False, f"Update error: {e}"

# Global instance
monitor = ModelChangeMonitor()

def check_and_update_if_changed():
    """Main function to check for changes and update if needed"""
    try:
        changed, message = monitor.check_for_changes()
        
        if changed:
            logger.info(f"Model changes detected: {message}")
            success, update_message = monitor.trigger_update()
            
            if success:
                logger.info(f"Automatic update successful: {update_message}")
                return True, f"Updated: {message}"
            else:
                logger.error(f"Automatic update failed: {update_message}")
                return False, f"Update failed: {update_message}"
        else:
            logger.debug(f"No changes: {message}")
            return False, message
            
    except Exception as e:
        logger.error(f"Error in change monitoring: {e}")
        return False, f"Monitoring error: {e}"