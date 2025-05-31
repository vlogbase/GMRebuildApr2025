#!/usr/bin/env python3
"""
Simple script to update pricing data directly
"""
import os
import requests
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_pricing_directly():
    """Update pricing data directly via database connection"""
    
    # Get database URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not found")
        return False
    
    # Get API key
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        logger.error("OPENROUTER_API_KEY not found")
        return False
    
    try:
        # Create direct database connection
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Fetch data from OpenRouter API
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        logger.info("Fetching model data from OpenRouter API...")
        response = requests.get(
            'https://openrouter.ai/api/v1/models',
            headers=headers,
            params={'limit': 1000, 'ready': 'all'},
            timeout=30
        )
        response.raise_for_status()
        
        models_data = response.json()
        models = models_data.get('data', [])
        logger.info(f"Retrieved {len(models)} models from API")
        
        # Process and update pricing
        markup_factor = 2.0
        updated_count = 0
        
        for model in models:
            model_id = model.get('id', '')
            if not model_id:
                continue
                
            # Extract pricing
            pricing = model.get('pricing', {})
            input_price_str = pricing.get('prompt', '0')
            output_price_str = pricing.get('completion', '0')
            
            try:
                input_price = float(input_price_str) if input_price_str else 0
                output_price = float(output_price_str) if output_price_str else 0
            except ValueError:
                logger.warning(f"Invalid pricing data for {model_id}, skipping")
                continue
            
            # Apply markup and convert to per-million pricing
            input_price_million = input_price * 1000000 * markup_factor
            output_price_million = output_price * 1000000 * markup_factor
            
            # Update database directly
            try:
                result = session.execute(
                    text("""
                        UPDATE open_router_model 
                        SET input_price_usd_million = :input_price,
                            output_price_usd_million = :output_price,
                            last_fetched_at = NOW()
                        WHERE model_id = :model_id
                    """),
                    {
                        'input_price': input_price_million,
                        'output_price': output_price_million,
                        'model_id': model_id
                    }
                )
                
                if result.rowcount > 0:
                    updated_count += 1
                    if updated_count % 50 == 0:
                        logger.info(f"Updated {updated_count} models...")
                        
            except Exception as e:
                logger.error(f"Error updating {model_id}: {e}")
                continue
        
        # Commit all changes
        session.commit()
        logger.info(f"Successfully updated pricing for {updated_count} models")
        
        # Show summary
        result = session.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN input_price_usd_million > 0 THEN 1 END) as with_pricing,
                   COUNT(CASE WHEN input_price_usd_million = 0 OR input_price_usd_million IS NULL THEN 1 END) as zero_pricing
            FROM open_router_model
        """))
        
        row = result.fetchone()
        logger.info(f"Database summary: {row.total} total models, {row.with_pricing} with pricing, {row.zero_pricing} with zero/null pricing")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"Error during pricing update: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

if __name__ == "__main__":
    success = update_pricing_directly()
    exit(0 if success else 1)