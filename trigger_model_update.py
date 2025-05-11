"""
Simple script to trigger the existing OpenRouter model update functionality.
This will refresh the models in the database, including PDF support information.
"""

import os
import sys
import logging
from flask import Flask
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a minimal Flask app with the database
from models import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

def main():
    """Run the update from price_updater module"""
    try:
        # First check if OpenRouter API key exists
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            logger.error("OPENROUTER_API_KEY not found in environment variables")
            return 1
        
        # Set up the application context
        with app.app_context():
            logger.info("Established Flask application context")
            
            # Verify database connection
            try:
                db.session.execute(text('SELECT 1'))
                logger.info("Database connection verified")
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                return 1
                
            # Import here to avoid any circular import issues
            from price_updater import fetch_and_store_openrouter_prices
            
            logger.info("Starting OpenRouter model update...")
            success = fetch_and_store_openrouter_prices()
            
            if success:
                # Query database for models with PDF support
                from models import OpenRouterModel
                pdf_models = OpenRouterModel.get_pdf_models()
                logger.info(f"OpenRouter model update completed successfully. Found {len(pdf_models)} models with PDF support.")
                return 0
            else:
                logger.error("Failed to update OpenRouter models")
                return 1
                
    except Exception as e:
        logger.error(f"Error updating OpenRouter models: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())