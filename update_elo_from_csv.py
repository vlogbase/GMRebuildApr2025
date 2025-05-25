#!/usr/bin/env python3
"""
Update ELO Scores from CSV

Updates the database with corrected ELO scores from the user-provided CSV file.
This script matches models by name and updates or clears ELO scores as needed.
"""

import os
import csv
import logging
import psycopg2
from contextlib import contextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """Get a direct database connection using the DATABASE_URL"""
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

def load_csv_data(filename):
    """Load ELO data from CSV file"""
    elo_mapping = {}
    
    try:
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                model_name = row['Model'].strip()
                elo_str = row['ELO'].strip()
                
                # Convert ELO to integer or None if empty
                if elo_str and elo_str.isdigit():
                    elo_score = int(elo_str)
                else:
                    elo_score = None
                
                elo_mapping[model_name] = elo_score
                
        logger.info(f"Loaded {len(elo_mapping)} models from CSV")
        return elo_mapping
        
    except Exception as e:
        logger.error(f"Error loading CSV file: {e}")
        return {}

def update_elo_scores(elo_mapping):
    """Update ELO scores in the database"""
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get all current models
        cursor.execute("SELECT model_id, name, elo_score FROM open_router_model ORDER BY name")
        db_models = cursor.fetchall()
        
        logger.info(f"Found {len(db_models)} models in database")
        
        updated_count = 0
        matched_count = 0
        cleared_count = 0
        
        for model_id, db_name, current_elo in db_models:
            # Look for exact match in CSV data
            new_elo = None
            
            # Try exact match first
            if db_name in elo_mapping:
                new_elo = elo_mapping[db_name]
                matched_count += 1
            
            # Update the ELO score (including setting to NULL if needed)
            if new_elo != current_elo:  # Only update if different
                cursor.execute(
                    "UPDATE open_router_model SET elo_score = %s WHERE model_id = %s",
                    (new_elo, model_id)
                )
                
                if new_elo is None and current_elo is not None:
                    cleared_count += 1
                    logger.info(f"Cleared ELO for: {db_name} (was {current_elo})")
                elif new_elo is not None:
                    if current_elo is None:
                        logger.info(f"Added ELO for: {db_name} -> {new_elo}")
                    else:
                        logger.info(f"Updated ELO for: {db_name}: {current_elo} -> {new_elo}")
                
                updated_count += 1
        
        # Commit all changes
        conn.commit()
        cursor.close()
        
        logger.info(f"✅ ELO score update complete!")
        logger.info(f"   - Total models in database: {len(db_models)}")
        logger.info(f"   - Models matched with CSV: {matched_count}")
        logger.info(f"   - Models updated: {updated_count}")
        logger.info(f"   - ELO scores cleared: {cleared_count}")
        
        return updated_count

def main():
    """Main function to run the ELO update"""
    csv_filename = "attached_assets/Models and ELO - Merged.csv"
    
    logger.info("=" * 60)
    logger.info("ELO Score Update from CSV")
    logger.info("=" * 60)
    
    # Load CSV data
    elo_mapping = load_csv_data(csv_filename)
    if not elo_mapping:
        logger.error("❌ Failed to load CSV data")
        return False
    
    # Update database
    try:
        updated_count = update_elo_scores(elo_mapping)
        
        if updated_count >= 0:
            logger.info("✅ ELO score update completed successfully!")
            return True
        else:
            logger.error("❌ ELO score update failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during update: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)