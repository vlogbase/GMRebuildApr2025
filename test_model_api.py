"""
This script tests OpenRouter model API access and database storage.
It helps verify which models are available via the API and stored in the database,
particularly focusing on PDF support detection.
"""

import os
import logging
import requests
from flask import Flask, jsonify
from database import db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app initialization
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
db.init_app(app)

@app.route('/check/<model_id>')
def check_model(model_id):
    """
    Check if a specific model exists in the database and show its details
    """
    try:
        # Import here to avoid circular imports
        from models import OpenRouterModel

        with app.app_context():
            # Check if model exists in database
            model = OpenRouterModel.query.get(model_id)
            if model:
                return jsonify({
                    'status': 'found',
                    'database_info': {
                        'model_id': model.model_id,
                        'name': model.name,
                        'supports_pdf': model.supports_pdf,
                        'is_active': model.model_is_active,
                        'description': model.description,
                        'is_multimodal': model.is_multimodal
                    }
                })
            else:
                # If not in database, check the API directly
                api_key = os.environ.get('OPENROUTER_API_KEY')
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'HTTP-Referer': 'https://gloriamundo.ai'
                }
                
                # First check with the models endpoint
                models_url = f'https://openrouter.ai/api/v1/models'
                models_response = requests.get(models_url, headers=headers)
                models_data = models_response.json() if models_response.status_code == 200 else None
                
                model_in_api = None
                if models_data and 'data' in models_data:
                    model_in_api = next((m for m in models_data['data'] if m.get('id') == model_id), None)
                
                if model_in_api:
                    # Model found in regular API listing
                    input_modalities = model_in_api.get('architecture', {}).get('input_modalities', [])
                    supports_pdf = 'file' in input_modalities
                    
                    return jsonify({
                        'status': 'api_only',
                        'api_info': {
                            'model_id': model_id,
                            'name': model_in_api.get('name'),
                            'input_modalities': input_modalities,
                            'supports_pdf': supports_pdf,
                            'description': model_in_api.get('description')
                        }
                    })
                else:
                    # Check model-specific endpoint as a last resort
                    model_url = f'https://openrouter.ai/api/v1/models/{model_id}'
                    model_response = requests.get(model_url, headers=headers)
                    
                    if model_response.status_code == 200:
                        specific_model_data = model_response.json()
                        input_modalities = specific_model_data.get('architecture', {}).get('input_modalities', [])
                        supports_pdf = 'file' in input_modalities
                        
                        return jsonify({
                            'status': 'api_direct_only',
                            'api_direct_info': {
                                'model_id': model_id,
                                'name': specific_model_data.get('name'),
                                'input_modalities': input_modalities, 
                                'supports_pdf': supports_pdf,
                                'description': specific_model_data.get('description')
                            }
                        })
                    else:
                        return jsonify({
                            'status': 'not_found',
                            'error': f'Model {model_id} not found in database or API'
                        }), 404
                        
    except Exception as e:
        logger.error(f"Error checking model {model_id}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)