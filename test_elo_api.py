#!/usr/bin/env python3
"""
Test ELO Integration - Check API Response

Verifies that the /api/get_model_prices endpoint includes ELO scores
and reports the integration status.
"""

import os
import sys
import json
import logging
import psycopg2
import requests
from contextlib import contextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """Get database connection"""
    connection = None
    try:
        database_url = os.environ.get('DATABASE_URL')
        connection = psycopg2.connect(database_url)
        yield connection
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if connection:
            connection.close()

def check_elo_integration_status():
    """Check the current status of ELO integration in the database"""
    logger.info("Checking ELO integration status...")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get summary statistics
        cursor.execute("""
            SELECT COUNT(*) as total_models,
                   COUNT(elo_score) as models_with_elo,
                   MAX(elo_score) as max_elo,
                   MIN(elo_score) as min_elo,
                   ROUND(AVG(elo_score)) as avg_elo
            FROM open_router_model 
            WHERE model_is_active = true;
        """)
        
        result = cursor.fetchone()
        
        if result:
            total, with_elo, max_elo, min_elo, avg_elo = result
            success_rate = (with_elo / total * 100) if total > 0 else 0
            
            logger.info(f"📊 ELO Integration Results:")
            logger.info(f"   ✅ Total active models: {total}")
            logger.info(f"   ✅ Models with ELO scores: {with_elo}")
            logger.info(f"   ✅ Success rate: {success_rate:.1f}%")
            
            if with_elo > 0:
                logger.info(f"   📈 ELO range: {min_elo} - {max_elo}")
                logger.info(f"   📊 Average ELO: {avg_elo}")
        
        # Show top ELO models
        cursor.execute("""
            SELECT model_id, elo_score 
            FROM open_router_model 
            WHERE elo_score IS NOT NULL AND model_is_active = true
            ORDER BY elo_score DESC 
            LIMIT 5;
        """)
        
        top_models = cursor.fetchall()
        if top_models:
            logger.info(f"🏆 Top 5 models by ELO score:")
            for model_id, elo in top_models:
                logger.info(f"     {model_id}: {elo}")
        
        cursor.close()
        return True

def test_api_response():
    """Test the API response to verify ELO scores are included"""
    logger.info("Testing API response for ELO scores...")
    
    # Add the current directory to Python path for imports
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Import Flask app and models
        from app import app
        from models import OpenRouterModel
        
        with app.app_context():
            # Get a few models with ELO scores to test
            test_models = OpenRouterModel.query.filter(
                OpenRouterModel.elo_score.isnot(None),
                OpenRouterModel.model_is_active == True
            ).limit(3).all()
            
            if not test_models:
                logger.warning("No models with ELO scores found for testing")
                return False
            
            logger.info(f"Found {len(test_models)} models with ELO scores for testing")
            
            # Test the API endpoint by importing the function directly
            from app import get_model_prices
            
            # Create a test request context
            with app.test_request_context():
                response = get_model_prices()
                
                # Parse the response
                if hasattr(response, 'get_json'):
                    data = response.get_json()
                else:
                    # Handle direct function call response
                    import json
                    data = json.loads(response.data)
                
                if data and 'prices' in data:
                    prices = data['prices']
                    
                    # Check if ELO scores are included
                    models_with_elo = 0
                    sample_model = None
                    
                    for model_id, model_data in prices.items():
                        if 'elo_score' in model_data and model_data['elo_score'] is not None:
                            models_with_elo += 1
                            if not sample_model:
                                sample_model = (model_id, model_data['elo_score'])
                    
                    logger.info(f"🎯 API Response Test Results:")
                    logger.info(f"   ✅ Total models in API response: {len(prices)}")
                    logger.info(f"   ✅ Models with ELO scores in API: {models_with_elo}")
                    
                    if sample_model:
                        logger.info(f"   📍 Sample: {sample_model[0]} has ELO {sample_model[1]}")
                        logger.info(f"   ✅ ELO scores are successfully included in API response!")
                        return True
                    else:
                        logger.warning("   ⚠️  No ELO scores found in API response")
                        return False
                else:
                    logger.error("   ❌ Invalid API response format")
                    return False
                    
    except Exception as e:
        logger.error(f"Error testing API response: {e}")
        return False

def main():
    """Run the ELO integration test"""
    logger.info("🔍 Testing LMSYS ELO Integration")
    logger.info("=" * 50)
    
    try:
        # Check database status
        db_success = check_elo_integration_status()
        
        if db_success:
            # Test API response
            api_success = test_api_response()
            
            if api_success:
                logger.info("🎉 ELO Integration Test SUCCESSFUL!")
                logger.info("   Your application now serves authentic LMSYS ELO scores")
                logger.info("   alongside pricing data for enhanced model selection!")
                return True
            else:
                logger.error("❌ API test failed - ELO scores not in response")
                return False
        else:
            logger.error("❌ Database test failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)