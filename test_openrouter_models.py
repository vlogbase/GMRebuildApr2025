#!/usr/bin/env python3
"""
Test script to verify that OpenRouter models are being retrieved from the database.
"""

import os
import sys
import logging
import json
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@contextmanager
def app_context():
    """Context manager to provide the Flask app context"""
    try:
        from app import app, db
        with app.app_context():
            yield db
    except Exception as e:
        logger.error(f"Failed to get app context: {e}")
        raise

def test_fetch_models_from_db():
    """
    Test fetching OpenRouter models from the database
    """
    with app_context() as db:
        try:
            # Import the model class
            from models import OpenRouterModel
            
            # Query all models
            all_models = db.session.query(OpenRouterModel).all()
            
            # Log summary
            logger.info(f"Found {len(all_models)} models in the database")
            
            # Log details of first few models
            for i, model in enumerate(all_models[:5]):
                logger.info(f"Model {i+1}: {model.model_id}")
                logger.info(f"  Name: {model.name}")
                logger.info(f"  Description: {model.description[:50]}..." if model.description else "  Description: None")
                logger.info(f"  Multimodal: {model.is_multimodal}, Free: {model.is_free}, Reasoning: {model.supports_reasoning}")
                logger.info(f"  Input price: ${model.input_price_usd_million:.2f} per million tokens")
                logger.info(f"  Output price: ${model.output_price_usd_million:.2f} per million tokens")
                logger.info(f"  Cost band: {model.cost_band}")
                logger.info(f"  Last fetched: {model.last_fetched_at}")
                
            return True
        except Exception as e:
            logger.error(f"Error fetching models from database: {e}")
            return False

def test_api_route():
    """
    Test the /models API route to ensure it returns data from the database
    """
    try:
        from app import app
        
        # Create a test client
        client = app.test_client()
        
        # Make a request to the models endpoint
        response = client.get('/models')
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"API request failed with status code {response.status_code}")
            return False
            
        # Parse the response
        models_data = json.loads(response.data)
        
        # Log summary
        logger.info(f"API returned {len(models_data)} models")
        
        # Log details of first few models
        for i, model in enumerate(models_data[:3]):
            logger.info(f"API Model {i+1}: {model.get('id')}")
            logger.info(f"  Name: {model.get('name')}")
            logger.info(f"  Context length: {model.get('context_length')}")
            
        return True
    except Exception as e:
        logger.error(f"Error testing API route: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Testing OpenRouter models from database...")
    
    # Test database fetch
    db_success = test_fetch_models_from_db()
    if not db_success:
        logger.error("Database test failed")
    else:
        logger.info("Database test passed successfully")
        
    # Test API route
    api_success = test_api_route()
    if not api_success:
        logger.error("API test failed")
    else:
        logger.info("API test passed successfully")
        
    return db_success and api_success

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("All tests completed successfully")
        sys.exit(0)
    else:
        logger.error("Tests failed")
        sys.exit(1)