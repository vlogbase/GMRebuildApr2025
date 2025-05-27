#!/usr/bin/env python3
"""
Direct ELO Score Update Script

Updates existing OpenRouter models with LMSYS ELO scores using the cached data.
"""

import os
import json
import logging
import psycopg2
from contextlib import contextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """Get a direct database connection"""
    connection = None
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL environment variable not found")
        
        connection = psycopg2.connect(database_url)
        yield connection
        
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if connection:
            connection.close()

def normalize_for_matching(model_id_or_name: str) -> str:
    """Normalize model identifiers for matching (same logic as lmsys_updater.py)"""
    if not model_id_or_name:
        return ""
    
    name = model_id_or_name.lower()
    name = name.replace("-", "").replace("_", "").replace(" ", "")
    name = name.replace(".", "").replace(":", "").replace("/", "")
    name = name.replace("(", "").replace(")", "").replace("[", "").replace("]", "")
    
    # Normalize common variations
    name = name.replace("chatgpt", "gpt")
    name = name.replace("gpt4o", "gpt4o")
    name = name.replace("gpt4", "gpt4")
    name = name.replace("claude3", "claude3")
    name = name.replace("gemini2", "gemini2")
    
    return name

def load_elo_cache():
    """Load LMSYS ELO cache from JSON file"""
    try:
        if not os.path.exists('lmsys_elo_cache.json'):
            logger.error("lmsys_elo_cache.json not found. Please run lmsys_updater.py first.")
            return {}
        
        with open('lmsys_elo_cache.json', 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        elo_mapping = cache_data.get('elo_mapping', {})
        logger.info(f"Loaded {len(elo_mapping)} ELO scores from cache")
        return elo_mapping
        
    except Exception as e:
        logger.error(f"Error loading ELO cache: {e}")
        return {}

def get_elo_score_for_model(model_id: str, elo_cache: dict) -> int:
    """Get ELO score for a specific OpenRouter model ID"""
    if not elo_cache:
        return None
    
    # Normalize the OpenRouter model ID for matching
    normalized_model = normalize_for_matching(model_id)
    
    # Direct lookup
    if normalized_model in elo_cache:
        return elo_cache[normalized_model]['elo_score']
    
    # Try partial matching for common patterns
    for lmsys_norm, data in elo_cache.items():
        # Check for key model family matches
        if ('gemini' in normalized_model and 'gemini' in lmsys_norm) or \
           ('claude' in normalized_model and 'claude' in lmsys_norm) or \
           ('gpt4' in normalized_model and 'gpt4' in lmsys_norm) or \
           ('llama' in normalized_model and 'llama' in lmsys_norm):
            logger.debug(f"Matched {model_id} -> {data['original_lmsys_name']} (ELO: {data['elo_score']})")
            return data['elo_score']
    
    return None

def update_model_elo_scores():
    """Update ELO scores for all models in the database"""
    # Load ELO cache
    elo_cache = load_elo_cache()
    if not elo_cache:
        logger.error("No ELO cache data available")
        return False
    
    updated_count = 0
    matched_count = 0
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get all models
        cursor.execute("SELECT model_id FROM open_router_model WHERE model_is_active = true;")
        models = cursor.fetchall()
        
        logger.info(f"Processing {len(models)} active models for ELO score assignment...")
        
        for (model_id,) in models:
            try:
                # Get ELO score for this model
                elo_score = get_elo_score_for_model(model_id, elo_cache)
                
                # Update the model with ELO score (even if None)
                cursor.execute("""
                    UPDATE open_router_model 
                    SET elo_score = %s 
                    WHERE model_id = %s;
                """, (elo_score, model_id))
                
                updated_count += 1
                
                if elo_score:
                    matched_count += 1
                    if matched_count <= 10:  # Log first 10 matches
                        logger.info(f"✅ Assigned ELO {elo_score} to {model_id}")
                
            except Exception as e:
                logger.error(f"Error updating {model_id}: {e}")
        
        # Commit all changes
        conn.commit()
        cursor.close()
    
    logger.info(f"✅ ELO score update complete!")
    logger.info(f"   - Models processed: {updated_count}")
    logger.info(f"   - Models with ELO scores: {matched_count}")
    logger.info(f"   - Matching rate: {matched_count/updated_count*100:.1f}%")
    
    return True

def verify_results():
    """Verify the ELO score assignment results"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get summary statistics
        cursor.execute("""
            SELECT COUNT(*) as total_models,
                   COUNT(elo_score) as models_with_elo,
                   MAX(elo_score) as max_elo,
                   MIN(elo_score) as min_elo,
                   AVG(elo_score) as avg_elo
            FROM open_router_model 
            WHERE model_is_active = true;
        """)
        
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            total, with_elo, max_elo, min_elo, avg_elo = result
            logger.info(f"📊 Results Summary:")
            logger.info(f"   - Total active models: {total}")
            logger.info(f"   - Models with ELO scores: {with_elo}")
            logger.info(f"   - ELO score range: {min_elo} - {max_elo}")
            logger.info(f"   - Average ELO: {avg_elo:.0f}" if avg_elo else "   - Average ELO: N/A")
            
            return True
        
        return False

def main():
    """Run the ELO score update process"""
    logger.info("🎯 Starting ELO score assignment for OpenRouter models...")
    
    try:
        # Update ELO scores
        success = update_model_elo_scores()
        
        if success:
            # Verify results
            verify_results()
            logger.info("🎉 ELO score integration completed successfully!")
            return True
        else:
            logger.error("❌ ELO score update failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ ELO score update failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)