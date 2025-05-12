"""
Script to check PDF support in OpenRouter model information.
"""
import os
import sys
import json
import logging
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_pdf_support():
    """
    Check PDF support for GPT-4o and Gemini models in the database.
    """
    try:
        # Get database URL from environment
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            return False
            
        # Create engine
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Query for GPT-4o and Gemini models
            query = text("""
                SELECT model_id, name, supports_pdf, is_multimodal, cost_band, input_price_usd_million 
                FROM open_router_model 
                WHERE model_id LIKE '%gpt-4o%' OR model_id LIKE '%gemini%'
                ORDER BY model_id
            """)
            
            result = conn.execute(query)
            rows = result.fetchall()
            
            if not rows:
                logger.info("No GPT-4o or Gemini models found in the database")
                return False
            
            logger.info(f"Found {len(rows)} GPT-4o and Gemini models:")
            for row in rows:
                model_id, name, supports_pdf, is_multimodal, cost_band, input_price = row
                logger.info(f"Model ID: {model_id}")
                logger.info(f"  Name: {name}")
                logger.info(f"  Supports PDF: {supports_pdf}")
                logger.info(f"  Is Multimodal: {is_multimodal}")
                logger.info(f"  Cost Band: {cost_band}")
                logger.info(f"  Input Price: {input_price}")
                logger.info("---")
            
            # Check how the model info is sent to the frontend
            query = text("""
                SELECT * FROM open_router_model LIMIT 1;
            """)
            result = conn.execute(query)
            row = result.fetchone()
            
            if row:
                logger.info("Database schema for open_router_model:")
                for column, value in zip(result.keys(), row):
                    logger.info(f"  {column}: {value}")
            
            return True
                
    except Exception as e:
        logger.error(f"Error checking PDF support: {e}")
        return False

if __name__ == "__main__":
    logger.info("Checking PDF support for GPT-4o and Gemini models...")
    success = check_pdf_support()
    if success:
        logger.info("Successfully checked PDF support")
    else:
        logger.error("Failed to check PDF support")
        sys.exit(1)