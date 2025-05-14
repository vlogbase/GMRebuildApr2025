"""
Workflow script to trigger a manual update of OpenRouter models in the database
"""

import logging
import time
from app import app as flask_app
from price_updater import fetch_and_store_openrouter_prices

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    """
    Run a manual update of OpenRouter models with enhanced parameters
    """
    logger.info("Starting OpenRouter model update...")
    
    with flask_app.app_context():
        success = fetch_and_store_openrouter_prices()
        
        if success:
            logger.info("Successfully updated OpenRouter models in the database")
        else:
            logger.error("Failed to update OpenRouter models")
            
    logger.info("Model update process complete")

if __name__ == "__main__":
    run()