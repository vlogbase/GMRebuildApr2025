#!/usr/bin/env python3
"""
Test script for OpenRouter model migrations and database access.

This script verifies that:
1. The migrations work correctly
2. The database model can be accessed
3. All required fields are present and populated
"""

import sys
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def log_model_stats(models):
    """Log statistics about the models"""
    if not models:
        logger.warning("No models found in database!")
        return
        
    logger.info(f"Found {len(models)} models in the database")
    
    # Count by type
    multimodal_count = len([m for m in models if m.is_multimodal])
    free_count = len([m for m in models if m.is_free])
    reasoning_count = len([m for m in models if m.supports_reasoning])
    
    # Count by cost band
    cost_bands = {}
    for model in models:
        band = model.cost_band or "none"
        cost_bands[band] = cost_bands.get(band, 0) + 1
        
    logger.info(f"Model capabilities: {multimodal_count} multimodal, {free_count} free, {reasoning_count} reasoning")
    logger.info(f"Cost bands: {cost_bands}")
    
    # Show a few example models for verification
    logger.info("Sample models:")
    for i, model in enumerate(models[:5]):
        logger.info(f"  Model {i+1}: {model.model_id} - {model.name}")
        logger.info(f"    Price: ${model.input_price_usd_million} per million input tokens, ${model.output_price_usd_million} per million output tokens")
        logger.info(f"    Capabilities: multimodal={model.is_multimodal}, free={model.is_free}, reasoning={model.supports_reasoning}")
        logger.info(f"    Cost band: {model.cost_band}")
        logger.info(f"    Created: {model.created_at}, Updated: {model.updated_at}, Last fetched: {model.last_fetched_at}")

def run_migration_test():
    """Run migration and test access to the database models"""
    try:
        # First, run the migrations to ensure tables and columns exist
        from run_openrouter_model_migration import run_migrations
        success = run_migrations()
        
        if not success:
            logger.error("Migration failed, aborting test")
            return False
            
        logger.info("Migration completed successfully, testing database access...")
        
        # Get a Flask app context to access the database
        from app import app, db
        from models import OpenRouterModel
        
        # Query all models from the database within app context
        with app.app_context():
            logger.info("Querying all models from the database...")
            all_models = OpenRouterModel.query.all()
        
        # Log statistics about the models
        log_model_stats(all_models)
        
        # Do all database operations within app context
        with app.app_context():
            # Test specific model lookup
            logger.info("Testing specific model access...")
            claude_model = OpenRouterModel.query.filter(OpenRouterModel.model_id.like('%claude%')).first()
            
            if claude_model:
                logger.info(f"Found Claude model: {claude_model.model_id} - {claude_model.name}")
                logger.info(f"Reasoning capability: {claude_model.supports_reasoning}")
            else:
                logger.warning("No Claude model found in database")
            
            # Test filter by capability
            logger.info("Testing filtering by capability...")
            multimodal_models = OpenRouterModel.query.filter(OpenRouterModel.is_multimodal == True).all()
            reasoning_models = OpenRouterModel.query.filter(OpenRouterModel.supports_reasoning == True).all()
            
            logger.info(f"Found {len(multimodal_models)} multimodal models")
            logger.info(f"Found {len(reasoning_models)} reasoning models")
            
            # Test get_models_by_cost_band method
            logger.info("Testing cost band filtering...")
            for band in ['$', '$$', '$$$', '$$$$']:
                models_in_band = OpenRouterModel.get_models_by_cost_band(band)
                logger.info(f"Found {len(models_in_band)} models in cost band {band}")
        
        logger.info("Database tests completed successfully")
        return True
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error(traceback.format_exc())
        return False
    except Exception as e:
        logger.error(f"Error during test: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Starting OpenRouter model migration test")
    success = run_migration_test()
    
    if success:
        logger.info("Test completed successfully")
        sys.exit(0)
    else:
        logger.error("Test failed")
        sys.exit(1)