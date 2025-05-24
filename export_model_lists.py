#!/usr/bin/env python3
"""
Export Model Lists for Manual ELO Mapping

Creates comprehensive CSV files of all OpenRouter models and all LMSYS models
to facilitate manual matching and review.
"""

import os
import json
import csv
import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def export_openrouter_models():
    """Export all OpenRouter models to CSV"""
    logger.info("Exporting all OpenRouter models...")
    
    database_url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    # Get all models (active and inactive) with all relevant fields
    cursor.execute("""
        SELECT 
            model_id,
            name,
            model_is_active,
            description,
            context_length,
            input_price_usd_million,
            output_price_usd_million,
            is_multimodal,
            cost_band,
            is_free,
            supports_reasoning,
            supports_pdf,
            elo_score,
            created_at,
            updated_at
        FROM open_router_model 
        ORDER BY model_is_active DESC, model_id;
    """)
    
    models = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Write to CSV
    filename = 'all_openrouter_models.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'openrouter_id',
            'display_name', 
            'is_active',
            'description',
            'context_length',
            'input_price_usd_million',
            'output_price_usd_million',
            'is_multimodal',
            'cost_band',
            'is_free',
            'supports_reasoning',
            'supports_pdf',
            'current_elo_score',
            'created_at',
            'updated_at'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for model in models:
            writer.writerow({
                'openrouter_id': model[0],
                'display_name': model[1] or model[0],  # Use ID as fallback if no name
                'is_active': 'YES' if model[2] else 'NO',
                'description': model[3] or '',
                'context_length': model[4] or '',
                'input_price_usd_million': model[5] or '',
                'output_price_usd_million': model[6] or '',
                'is_multimodal': 'YES' if model[7] else 'NO',
                'cost_band': model[8] or '',
                'is_free': 'YES' if model[9] else 'NO',
                'supports_reasoning': 'YES' if model[10] else 'NO',
                'supports_pdf': 'YES' if model[11] else 'NO',
                'current_elo_score': model[12] or '',
                'created_at': model[13] or '',
                'updated_at': model[14] or ''
            })
    
    active_count = sum(1 for model in models if model[2])
    total_count = len(models)
    
    logger.info(f"Exported {total_count} total OpenRouter models to {filename}")
    logger.info(f"  - Active models: {active_count}")
    logger.info(f"  - Inactive models: {total_count - active_count}")
    
    return filename

def export_lmsys_models():
    """Export all LMSYS models to CSV"""
    logger.info("Exporting all LMSYS models...")
    
    try:
        with open('lmsys_elo_cache.json', 'r') as f:
            cache_data = json.load(f)
        
        elo_mapping = cache_data.get('elo_mapping', {})
        
        # Convert to list for CSV export
        lmsys_models = []
        for normalized_name, data in elo_mapping.items():
            lmsys_models.append({
                'lmsys_model_name': data['original_lmsys_name'],
                'normalized_name': normalized_name,
                'elo_score': data['elo_score'],
                'rank': data.get('rank', ''),
                'organization': data.get('organization', ''),
                'model_family': data.get('model_family', ''),
                'model_type': data.get('model_type', '')
            })
        
        # Sort by ELO score (descending)
        lmsys_models.sort(key=lambda x: x['elo_score'], reverse=True)
        
        # Write to CSV
        filename = 'all_lmsys_models.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'lmsys_model_name',
                'normalized_name',
                'elo_score',
                'rank',
                'organization',
                'model_family',
                'model_type'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(lmsys_models)
        
        logger.info(f"Exported {len(lmsys_models)} LMSYS models to {filename}")
        logger.info(f"  - ELO range: {min(m['elo_score'] for m in lmsys_models)} - {max(m['elo_score'] for m in lmsys_models)}")
        
        return filename
        
    except Exception as e:
        logger.error(f"Error loading LMSYS cache: {e}")
        return None

def main():
    """Export both model lists"""
    logger.info("🗂️  Exporting Comprehensive Model Lists")
    logger.info("=" * 50)
    
    try:
        # Export OpenRouter models
        or_file = export_openrouter_models()
        
        # Export LMSYS models
        lmsys_file = export_lmsys_models()
        
        logger.info("🎉 Export completed successfully!")
        logger.info("Files created:")
        if or_file:
            logger.info(f"  - {or_file} (All OpenRouter models)")
        if lmsys_file:
            logger.info(f"  - {lmsys_file} (All LMSYS models)")
        
        logger.info("\nYou can now:")
        logger.info("  1. Open both CSV files in a spreadsheet application")
        logger.info("  2. Manually match OpenRouter IDs to LMSYS model names")
        logger.info("  3. Use the authentic ELO scores for accurate model ranking")
        
        return True
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)