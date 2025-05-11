"""
Script to Update Database with PDF Support Information

This script updates existing models in the database with information about
PDF file support based on the OpenRouter API response.
"""

import os
import logging
import requests
from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the necessary models
from models import db, OpenRouterModel

# Create a minimal Flask app for the database context
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

def get_pdf_capable_model_ids():
    """Directly fetch from OpenRouter API and get IDs of PDF-capable models"""
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
        
        # Extract model IDs with PDF support
        pdf_model_ids = []
        for model in models_data:
            model_id = model.get('id', '')
            architecture = model.get('architecture', {})
            
            # Check for PDF support
            supports_pdf = False
            if architecture:
                input_modalities = architecture.get('input_modalities', [])
                supports_pdf = 'file' in input_modalities
            
            if supports_pdf:
                pdf_model_ids.append(model_id)
        
        return pdf_model_ids
        
    except Exception as e:
        logger.error(f"Error fetching models from OpenRouter: {e}")
        return []

def update_database_pdf_support():
    """Update the database with PDF support information"""
    pdf_model_ids = get_pdf_capable_model_ids()
    if not pdf_model_ids:
        logger.error("No PDF-capable models found")
        return False
    
    logger.info(f"Found {len(pdf_model_ids)} PDF-capable models")
    
    try:
        # First, reset all models' PDF support to False
        db.session.query(OpenRouterModel).update({OpenRouterModel.supports_pdf: False})
        
        # Then, set PDF support to True for identified models
        for model_id in pdf_model_ids:
            model = OpenRouterModel.query.get(model_id)
            if model:
                model.supports_pdf = True
                logger.info(f"Updated PDF support for {model.name} ({model_id})")
            else:
                logger.warning(f"Model {model_id} not found in database")
        
        # Commit the changes
        db.session.commit()
        logger.info("Database updated successfully with PDF support information")
        return True
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating PDF support: {e}")
        return False
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating database with PDF support: {e}")
        return False

def main():
    """Main function to run the script"""
    with app.app_context():
        logger.info("Starting database update with PDF support information...")
        success = update_database_pdf_support()
        
        if success:
            # Verify the update by counting PDF-capable models in the database
            pdf_models = OpenRouterModel.get_pdf_models()
            logger.info(f"Database update completed. Found {len(pdf_models)} models with PDF support in database:")
            for model in pdf_models:
                logger.info(f"- {model.name} ({model.model_id})")
        else:
            logger.error("Failed to update database with PDF support information")

if __name__ == "__main__":
    main()