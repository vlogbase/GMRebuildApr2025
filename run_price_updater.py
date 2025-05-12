"""
Script to run the price_updater.py with the proper Flask application context.
This is a simpler approach that avoids circular imports.
"""
import os
import sys
import logging
from flask import Flask
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

def run_price_updater():
    """
    Run the price_updater.py script with the proper Flask application context.
    """
    try:
        # Create a minimal Flask app
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
        
        # Create DB
        db = SQLAlchemy(model_class=Base)
        db.init_app(app)
        
        # Import the modules we need, but only after app is created
        with app.app_context():
            # Import models to ensure tables exist
            from models import OpenRouterModel
            
            # Import price_updater but don't override its imports
            # Just use our app context for its operations
            import price_updater
            
            # Run the price fetching function
            logger.info("Fetching and storing OpenRouter model prices...")
            success = price_updater.fetch_and_store_openrouter_prices()
            
            if success:
                logger.info("✅ Successfully fetched and stored model prices!")
                
                # Check if PDF-capable models are correctly identified
                logger.info("Checking key models for PDF support...")
                test_models = [
                    "openai/gpt-4o-2024-11-20",
                    "google/gemini-2.5-pro-preview"
                ]
                
                for model_id in test_models:
                    model = OpenRouterModel.query.get(model_id)
                    if model:
                        logger.info(f"Model: {model_id}")
                        logger.info(f"  Name: {model.name}")
                        logger.info(f"  Supports PDF: {model.supports_pdf}")
                        logger.info(f"  Is Multimodal: {model.is_multimodal}")
                        logger.info("---")
                    else:
                        logger.warning(f"Model {model_id} not found in database")
                
                return True
            else:
                logger.error("❌ Failed to fetch and store model prices")
                return False
        
    except Exception as e:
        logger.error(f"Error running price_updater: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Running price_updater.py with Flask application context...")
    success = run_price_updater()
    if success:
        logger.info("✅ Successfully ran price_updater.py!")
        sys.exit(0)
    else:
        logger.error("❌ Failed to run price_updater.py")
        sys.exit(1)