#!/usr/bin/env python3
"""
Generate Proposed ELO Mappings

Creates accurate mappings between OpenRouter models and LMSYS ELO scores
by preserving model variant details and using string similarity metrics.
"""

import os
import json
import csv
import psycopg2
from difflib import SequenceMatcher
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def refined_normalize_for_matching(model_name):
    """
    Refined normalization that preserves variant-specific details
    while still enabling matching between different naming conventions.
    """
    if not model_name:
        return ""
    
    name = model_name.lower()
    
    # Remove common separators but preserve important details
    name = name.replace("-", "").replace("_", "").replace(" ", "")
    name = name.replace(".", "").replace(":", "").replace("/", "")
    name = name.replace("(", "").replace(")", "")
    
    # Preserve important model differentiators
    # Keep version numbers, size indicators, and variant names
    
    # Handle specific provider patterns while preserving variants
    name = name.replace("chatgpt", "gpt")
    
    # Normalize common variants but keep them distinct
    # Keep opus, sonnet, haiku distinct
    # Keep version numbers like 3.5, 4.0, 2.5 distinct
    # Keep size indicators like 70b, 8x22b distinct
    # Keep date stamps like 20240229 distinct
    
    return name

def calculate_similarity(str1, str2):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, str1, str2).ratio() * 100

def load_openrouter_models():
    """Load active OpenRouter models from database"""
    logger.info("Loading OpenRouter models from database...")
    
    database_url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT model_id, name 
        FROM open_router_model 
        WHERE model_is_active = true 
        ORDER BY model_id;
    """)
    
    models = []
    for model_id, model_name in cursor.fetchall():
        models.append({
            'id': model_id,
            'name': model_name or model_id
        })
    
    cursor.close()
    conn.close()
    
    logger.info(f"Loaded {len(models)} active OpenRouter models")
    return models

def load_lmsys_elo_data():
    """Load LMSYS ELO data from cache"""
    logger.info("Loading LMSYS ELO data from cache...")
    
    try:
        with open('lmsys_elo_cache.json', 'r') as f:
            cache_data = json.load(f)
        
        elo_mapping = cache_data.get('elo_mapping', {})
        logger.info(f"Loaded {len(elo_mapping)} LMSYS ELO scores")
        return elo_mapping
    except Exception as e:
        logger.error(f"Error loading LMSYS cache: {e}")
        return {}

def find_model_matches(openrouter_models, lmsys_data):
    """Find potential matches between OpenRouter and LMSYS models"""
    logger.info("Analyzing model matches...")
    
    matches = []
    unmatched = []
    
    for or_model in openrouter_models:
        or_id = or_model['id']
        or_name = or_model['name']
        
        # Normalize the OpenRouter model for matching
        or_normalized = refined_normalize_for_matching(or_id)
        or_name_normalized = refined_normalize_for_matching(or_name)
        
        best_matches = []
        
        # Check against all LMSYS models
        for lmsys_normalized, lmsys_data_entry in lmsys_data.items():
            lmsys_original = lmsys_data_entry['original_lmsys_name']
            lmsys_elo = lmsys_data_entry['elo_score']
            
            # Calculate similarity scores
            id_similarity = calculate_similarity(or_normalized, lmsys_normalized)
            name_similarity = calculate_similarity(or_name_normalized, lmsys_normalized)
            
            # Use the higher of the two similarities
            max_similarity = max(id_similarity, name_similarity)
            
            # Consider matches with similarity > 70%
            if max_similarity >= 70:
                match_reasoning = []
                
                if id_similarity >= 85:
                    match_reasoning.append("High ID similarity")
                if name_similarity >= 85:
                    match_reasoning.append("High name similarity")
                if or_normalized == lmsys_normalized:
                    match_reasoning.append("Exact normalized match")
                if not match_reasoning:
                    match_reasoning.append("Moderate similarity match")
                
                best_matches.append({
                    'lmsys_original': lmsys_original,
                    'lmsys_elo': lmsys_elo,
                    'similarity': max_similarity,
                    'reasoning': "; ".join(match_reasoning),
                    'id_sim': id_similarity,
                    'name_sim': name_similarity
                })
        
        # Sort matches by similarity score
        best_matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        if best_matches:
            # Include top matches (similarity >= 80% or top 3 matches if any are >= 70%)
            high_confidence_matches = [m for m in best_matches if m['similarity'] >= 80]
            if not high_confidence_matches and best_matches:
                high_confidence_matches = best_matches[:3]  # Top 3 if none are high confidence
            
            for match in high_confidence_matches:
                matches.append({
                    'openrouter_model_id': or_id,
                    'openrouter_model_name': or_name,
                    'proposed_lmsys_model_name': match['lmsys_original'],
                    'proposed_lmsys_elo_score': match['lmsys_elo'],
                    'match_confidence_score': round(match['similarity'], 2),
                    'notes_or_reasoning': match['reasoning'],
                    'id_similarity': round(match['id_sim'], 2),
                    'name_similarity': round(match['name_sim'], 2)
                })
        else:
            unmatched.append({
                'openrouter_model_id': or_id,
                'openrouter_model_name': or_name,
                'proposed_lmsys_model_name': 'NO_MATCH_FOUND',
                'proposed_lmsys_elo_score': None,
                'match_confidence_score': 0,
                'notes_or_reasoning': 'No similar LMSYS model found (similarity < 70%)',
                'id_similarity': 0,
                'name_similarity': 0
            })
    
    logger.info(f"Found potential matches for {len([m for m in matches if m['match_confidence_score'] >= 80])} models (high confidence)")
    logger.info(f"Found potential matches for {len(matches)} total model-pairs")
    logger.info(f"Found {len(unmatched)} unmatched models")
    
    return matches + unmatched

def save_proposed_mappings(mappings):
    """Save proposed mappings to CSV and JSON files"""
    logger.info("Saving proposed mappings...")
    
    # Save as CSV
    csv_filename = 'proposed_elo_mappings.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'openrouter_model_id',
            'openrouter_model_name', 
            'proposed_lmsys_model_name',
            'proposed_lmsys_elo_score',
            'match_confidence_score',
            'notes_or_reasoning',
            'id_similarity',
            'name_similarity'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mappings)
    
    # Save as JSON for easier programmatic access
    json_filename = 'proposed_elo_mappings.json'
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(mappings, jsonfile, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved proposed mappings to {csv_filename} and {json_filename}")
    
    # Generate summary statistics
    high_confidence = len([m for m in mappings if m['match_confidence_score'] >= 90])
    medium_confidence = len([m for m in mappings if 80 <= m['match_confidence_score'] < 90])
    low_confidence = len([m for m in mappings if 70 <= m['match_confidence_score'] < 80])
    no_match = len([m for m in mappings if m['match_confidence_score'] == 0])
    
    logger.info(f"Summary:")
    logger.info(f"  High confidence matches (>=90%): {high_confidence}")
    logger.info(f"  Medium confidence matches (80-89%): {medium_confidence}")
    logger.info(f"  Low confidence matches (70-79%): {low_confidence}")
    logger.info(f"  No matches found: {no_match}")

def main():
    """Generate proposed ELO mappings for review"""
    logger.info("🎯 Generating Proposed ELO Mappings")
    logger.info("=" * 50)
    
    try:
        # Load data
        openrouter_models = load_openrouter_models()
        lmsys_data = load_lmsys_elo_data()
        
        if not openrouter_models:
            logger.error("No OpenRouter models found")
            return False
            
        if not lmsys_data:
            logger.error("No LMSYS ELO data found")
            return False
        
        # Find matches
        proposed_mappings = find_model_matches(openrouter_models, lmsys_data)
        
        # Save results
        save_proposed_mappings(proposed_mappings)
        
        logger.info("🎉 Proposed ELO mappings generated successfully!")
        logger.info("Please review the files:")
        logger.info("  - proposed_elo_mappings.csv (for manual review)")
        logger.info("  - proposed_elo_mappings.json (for programmatic access)")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating mappings: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)