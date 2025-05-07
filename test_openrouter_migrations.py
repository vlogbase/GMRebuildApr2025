#!/usr/bin/env python3
"""
Test script for OpenRouter model migrations

This script can be run directly to execute the migrations
outside of the main application startup flow.
"""

import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_migrations():
    """Run the migrations for testing"""
    logger.info("Testing OpenRouter migrations...")
    
    try:
        from migrations_openrouter_model import run_migrations
        success = run_migrations()
        
        if success:
            logger.info("Migrations completed successfully")
            return True
        else:
            logger.error("Migrations failed")
            return False
            
    except Exception as e:
        logger.exception(f"Error running migrations: {e}")
        return False

def verify_models():
    """Verify that models are in the database"""
    try:
        from flask import Flask
        from app import db
        from models import OpenRouterModel
        
        # Create a minimal app context
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost:5432/postgres"
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        
        # Initialize the app with the db
        db.init_app(app)
        
        with app.app_context():
            # Check how many models are in the database
            model_count = OpenRouterModel.query.count()
            logger.info(f"Found {model_count} models in the database")
            
            # Get a sample of models
            sample_models = OpenRouterModel.query.limit(5).all()
            for model in sample_models:
                logger.info(f"  - {model.model_id}: {model.name} ({model.cost_band})")
            
            return model_count > 0
            
    except Exception as e:
        logger.exception(f"Error verifying models: {e}")
        return False

if __name__ == "__main__":
    # Run the migrations
    migration_success = test_migrations()
    
    if migration_success:
        # Verify that models are in the database
        verification_success = verify_models()
        
        if verification_success:
            logger.info("Test completed successfully - models verified in database")
            sys.exit(0)
        else:
            logger.error("Test failed - could not verify models in database")
            sys.exit(1)
    else:
        logger.error("Test failed - migrations failed")
        sys.exit(1)