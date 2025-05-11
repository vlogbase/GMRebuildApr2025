"""
Script to directly update PDF support in the database via SQL
instead of using ORM due to circular import issues.
"""

import os
import json
import logging
import psycopg2
from psycopg2.extras import execute_values

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_pdf_support_in_database():
    """Update PDF support flags in the database using SQL"""
    # First check if we have the JSON file with PDF-capable models
    if not os.path.exists('pdf_capable_models.json'):
        logger.error("pdf_capable_models.json not found. Run check_pdf_support.py first.")
        return False
    
    # Load the PDF-capable models
    with open('pdf_capable_models.json', 'r') as f:
        pdf_models = json.load(f)
    
    pdf_model_ids = [model['id'] for model in pdf_models]
    
    if not pdf_model_ids:
        logger.error("No PDF-capable models found in json file")
        return False
    
    logger.info(f"Found {len(pdf_model_ids)} PDF-capable models to update in database")
    
    # Connect to the database
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL not found in environment variables")
            return False
        
        logger.info("Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # First, reset all models' PDF support to False
        logger.info("Resetting all models' PDF support to False")
        cursor.execute("UPDATE open_router_model SET supports_pdf = FALSE")
        
        # Then, set PDF support to True for identified models
        logger.info("Setting PDF support to True for PDF-capable models")
        models_tuple = tuple(pdf_model_ids)
        # Use a different approach if we only have one model
        if len(pdf_model_ids) == 1:
            cursor.execute("UPDATE open_router_model SET supports_pdf = TRUE WHERE model_id = %s", (pdf_model_ids[0],))
        else:
            cursor.execute("UPDATE open_router_model SET supports_pdf = TRUE WHERE model_id IN %s", (models_tuple,))
        
        # Commit the changes
        conn.commit()
        
        # Check how many models were updated
        cursor.execute("SELECT COUNT(*) FROM open_router_model WHERE supports_pdf = TRUE")
        updated_count = cursor.fetchone()[0]
        logger.info(f"Updated {updated_count} models in database with PDF support")
        
        # Get the updated models
        cursor.execute("SELECT model_id, name FROM open_router_model WHERE supports_pdf = TRUE")
        updated_models = cursor.fetchall()
        logger.info("Models with PDF support in database:")
        for model in updated_models:
            logger.info(f"- {model[1]} ({model[0]})")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating database with PDF support: {e}")
        return False

if __name__ == "__main__":
    update_pdf_support_in_database()