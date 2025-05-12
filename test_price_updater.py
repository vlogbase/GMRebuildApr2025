"""
Script to test the price_updater.py functionality.
This verifies that the fix for "Working outside of application context" error is effective.
"""
import os
import sys
import logging
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_app():
    """Create a minimal Flask app for testing."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    return app

def test_price_updater():
    """
    Test the price_updater.py module with properly set application context.
    """
    try:
        # First, override the app import in price_updater
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Create a test app
        test_app = create_test_app()
        
        # Explicitly import our app first to avoid circular imports
        import app as original_app
        
        # Now import price_updater
        import price_updater
        
        # Override app and db in price_updater
        price_updater.app = original_app.app
        price_updater.db = original_app.db
        
        # Test fetching and storing prices
        logger.info("Testing fetch_and_store_openrouter_prices()...")
        success = price_updater.fetch_and_store_openrouter_prices()
        
        if success:
            logger.info("✅ Successfully fetched and stored OpenRouter prices!")
        else:
            logger.error("❌ Failed to fetch and store OpenRouter prices")
        
        # Test get_model_cost
        logger.info("Testing get_model_cost()...")
        test_models = [
            "anthropic/claude-3-opus-20240229", 
            "openai/gpt-4o-2024-11-20",
            "google/gemini-2.5-pro-preview"
        ]
        
        for model_id in test_models:
            model_cost = price_updater.get_model_cost(model_id)
            logger.info(f"Model: {model_id}")
            logger.info(f"  Prompt cost: {model_cost.get('prompt_cost_per_million', 'N/A')}")
            logger.info(f"  Completion cost: {model_cost.get('completion_cost_per_million', 'N/A')}")
            logger.info(f"  Cost band: {model_cost.get('cost_band', 'N/A')}")
            logger.info(f"  Source: {model_cost.get('source', 'fallback')}")
            logger.info("---")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing price_updater: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Testing price_updater.py...")
    success = test_price_updater()
    if success:
        logger.info("✅ Successfully tested price_updater.py!")
        sys.exit(0)
    else:
        logger.error("❌ Failed to test price_updater.py")
        sys.exit(1)