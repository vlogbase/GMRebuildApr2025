"""
Minimal context test for app.py
"""
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import app with main application
logger.info("Importing app.py...")
try:
    from app import app, db, scheduled_price_update_job
    logger.info("Successfully imported app and scheduled_price_update_job")
    
    # Test with app context
    logger.info("Testing app.app_context()")
    with app.app_context():
        logger.info("Inside app context")
        
        # Import models and try to access the database
        from models import OpenRouterModel
        model_count = OpenRouterModel.query.count()
        logger.info(f"Found {model_count} models in the database")
        
        # Try our price update function
        logger.info("Testing price update function (this will run inside the existing context)")
        success = scheduled_price_update_job()
        
        if success:
            logger.info("Price update function completed successfully within app context!")
            model_count = OpenRouterModel.query.count()
            logger.info(f"After update: Found {model_count} models in the database")
        else:
            logger.error("Price update function failed")
    
    logger.info("Test completed")
except Exception as e:
    logger.error(f"Error occurred: {e}")
    import traceback
    logger.error(traceback.format_exc())