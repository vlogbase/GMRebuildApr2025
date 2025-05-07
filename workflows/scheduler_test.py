"""
Simple script to test the scheduler functionality and model data fetching.
"""

import sys
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to import app
sys.path.append(str(Path(__file__).parent.parent))

def run():
    """
    Run the Flask application with error handling and logging.
    """
    try:
        logger.info("Testing scheduler and model data fetching...")
        
        import app
        
        # Wait for the scheduler to initialize
        time.sleep(2)
        
        # Check if the scheduler is running
        if hasattr(app, 'scheduler') and app.scheduler:
            if app.scheduler.running:
                logger.info("✓ Scheduler is running")
                # Get the scheduled jobs
                jobs = app.scheduler.get_jobs()
                job_ids = [job.id for job in jobs]
                logger.info(f"✓ Scheduled jobs: {job_ids}")
            else:
                logger.error("✗ Scheduler is not running")
        else:
            logger.error("✗ Scheduler is not initialized")
        
        # Check if model data is available
        if hasattr(app, 'OPENROUTER_MODELS_INFO') and app.OPENROUTER_MODELS_INFO:
            logger.info(f"✓ Model data available: {len(app.OPENROUTER_MODELS_INFO)} models")
            
            # Log a few models as a sample
            sample_size = min(3, len(app.OPENROUTER_MODELS_INFO))
            for i in range(sample_size):
                model = app.OPENROUTER_MODELS_INFO[i]
                logger.info(f"  - Model {i+1}: {model.get('id')} - {model.get('name')}")
        else:
            logger.error("✗ No model data available")
        
        # Check the price cache
        from price_updater import model_prices_cache
        if model_prices_cache and model_prices_cache.get('prices'):
            logger.info(f"✓ Price cache available: {len(model_prices_cache['prices'])} models")
            logger.info(f"✓ Last updated: {model_prices_cache.get('last_updated')}")
            
            # Log a few prices as a sample
            sample_keys = list(model_prices_cache['prices'].keys())[:3]
            for key in sample_keys:
                price_data = model_prices_cache['prices'][key]
                logger.info(f"  - {key}: Input: ${price_data.get('input_price'):.6f}/M, Output: ${price_data.get('output_price'):.6f}/M")
        else:
            logger.error("✗ No price cache available")
        
        # Wait for potential async operations to complete
        logger.info("Test completed. The application will continue running in the background.")
        
    except Exception as e:
        logger.error(f"Error testing scheduler: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    run()