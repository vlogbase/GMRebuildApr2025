"""
Script to directly modify price_updater.py to fix the "Working outside of application context" error.
This script does not execute price_updater.py but rather modifies it.
"""
import os
import sys
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def modify_price_updater():
    """
    Modify price_updater.py to include application context.
    """
    try:
        # Define the file path
        file_path = 'price_updater.py'
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} does not exist")
            return False
        
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Modify the import section
        import_pattern = r'import os\nimport time\nimport logging\nimport requests\nfrom datetime import datetime\nfrom sqlalchemy\.exc import SQLAlchemyError'
        import_replacement = """import os
import time
import logging
import requests
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app

# Import the Flask app for application context
try:
    from app import app, db
except ImportError as e:
    logger.error(f"Failed to import app or db: {e}")
    app = None
    db = None"""
        
        # Replace the import section
        modified_content = re.sub(import_pattern, import_replacement, content)
        
        # Modify the database access in fetch_and_store_openrouter_prices
        db_pattern = r'# Store models in the database \(This is the new primary storage method\)\n        try:\n            # Import here to avoid circular imports\n            from app import db\n            from models import OpenRouterModel\n            \n            updated_count = 0\n            new_count = 0'
        db_replacement = """# Store models in the database (This is the new primary storage method)
        try:
            # Import here to avoid circular imports
            from models import OpenRouterModel
            
            # Check if we have valid app and db references
            if app is None or db is None:
                logger.error("Cannot store models in database: app or db is None")
                return False
                
            # Use application context for all database operations
            with app.app_context():
                updated_count = 0
                new_count = 0"""
        
        # Replace the database access section
        modified_content = re.sub(db_pattern, db_replacement, modified_content)
        
        # Modify the get_model_cost function
        model_cost_pattern = r'def get_model_cost\(model_id: str\) -> dict:\n    """[\s\S]+?    try:\n        # Try to get model info from the database first \(most reliable\)\n        from models import OpenRouterModel\n        \n        db_model = OpenRouterModel\.query\.get\(model_id\)'
        model_cost_replacement = """def get_model_cost(model_id: str) -> dict:
    \"""
    Get the cost per million tokens and cost band for a specific model.
    This function now primarily uses the database but falls back to cache and then to defaults.
    
    Args:
        model_id (str): The ID of the model
        
    Returns:
        dict: Dictionary containing prompt_cost_per_million, completion_cost_per_million, and cost_band
    \"""
    try:
        # Try to get model info from the database first (most reliable)
        from models import OpenRouterModel
        
        # Check if we have valid app reference
        if app is None:
            logger.warning("Cannot query database: app is None")
        else:
            # Use application context for database query
            with app.app_context():
                db_model = OpenRouterModel.query.get(model_id)"""
        
        # Replace the get_model_cost section
        modified_content = re.sub(model_cost_pattern, model_cost_replacement, modified_content)
        
        # Add application context for the second database query in get_model_cost
        second_query_pattern = r'# Try database lookup again after the fresh fetch\n        db_model = OpenRouterModel\.query\.get\(model_id\)'
        second_query_replacement = """# Check if we have valid app reference
        if app is None:
            logger.warning("Cannot query database after refresh: app is None")
        else:
            # Use application context for database query
            with app.app_context():
                # Try database lookup again after the fresh fetch
                from models import OpenRouterModel
                db_model = OpenRouterModel.query.get(model_id)"""
        
        # Replace the second query section
        modified_content = re.sub(second_query_pattern, second_query_replacement, modified_content)
        
        # Write the modified content back to the file
        with open(file_path, 'w') as f:
            f.write(modified_content)
        
        logger.info(f"Successfully modified {file_path}")
        
        # Show the first 50 lines of the modified file for verification
        with open(file_path, 'r') as f:
            head = "\n".join(f.readlines()[:50])
        logger.info(f"First 50 lines of modified file:\n{head}\n...")
        
        return True
        
    except Exception as e:
        logger.error(f"Error modifying {file_path}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Modifying price_updater.py...")
    success = modify_price_updater()
    if success:
        logger.info("✅ Successfully modified price_updater.py with application context!")
        sys.exit(0)
    else:
        logger.error("❌ Failed to modify price_updater.py")
        sys.exit(1)