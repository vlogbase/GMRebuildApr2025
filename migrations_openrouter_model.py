"""
Migrations for OpenRouter Model Database Persistence

This script creates the OpenRouterModel table and populates it with data 
from the OpenRouter API for new and existing installations of the application.
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to the path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@contextmanager
def app_context():
    """Context manager to provide the Flask app context"""
    try:
        from app import app, db
        with app.app_context():
            yield db
    except Exception as e:
        logger.error(f"Failed to get app context: {e}")
        raise

def check_table_exists():
    """Check if the OpenRouterModel table exists in the database"""
    with app_context() as db:
        try:
            result = db.session.execute("SELECT to_regclass('public.open_router_model');").scalar()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking if table exists: {e}")
            return False

def create_tables():
    """Create the OpenRouterModel table if it doesn't exist"""
    with app_context() as db:
        try:
            # Import the model class
            from models import OpenRouterModel
            
            # Create the table
            if not check_table_exists():
                logger.info("Creating OpenRouterModel table...")
                db.metadata.create_all(db.engine, tables=[OpenRouterModel.__table__])
                logger.info("OpenRouterModel table created successfully")
                return True
            else:
                logger.info("OpenRouterModel table already exists")
                return True
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False

def fetch_and_populate_models():
    """Fetch models from OpenRouter API and populate the database"""
    try:
        # First check if we have an API key
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            logger.error("OPENROUTER_API_KEY not found in environment variables")
            return False

        # Define headers for OpenRouter API
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Fetch models from OpenRouter
        logger.info("Fetching model data from OpenRouter API...")
        
        # Log the API request details (without exposing the full key)
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        logger.debug(f"API Request URL: https://openrouter.ai/api/v1/models")
        logger.debug(f"Using API key: {masked_key}")
        
        response = requests.get(
            'https://openrouter.ai/api/v1/models',
            headers=headers,
            timeout=15.0
        )
        
        # Log response status
        logger.debug(f"OpenRouter API response status code: {response.status_code}")
        
        # Check response status
        response.raise_for_status()
        
        # Parse response JSON
        models_data = response.json()
        
        # Log response data (limited for brevity)
        data_count = len(models_data.get('data', []))
        logger.debug(f"Received data for {data_count} models from OpenRouter API")
        
        # Now store the models in the database
        with app_context() as db:
            from models import OpenRouterModel
            
            updated_count = 0
            new_count = 0
            
            # Process models and store in the database
            markup_factor = 2.0  # Our markup for pricing
            
            for model in models_data.get('data', []):
                model_id = model.get('id', '')
                
                # Skip if model_id is empty
                if not model_id:
                    continue
                    
                # Extract pricing information
                pricing = model.get('pricing', {})
                input_price_str = pricing.get('prompt', '0') 
                output_price_str = pricing.get('completion', '0')
                
                # Convert string prices to float, handling any format issues
                try:
                    input_price = float(input_price_str) if input_price_str else 0
                except ValueError:
                    logger.warning(f"Invalid input price format for {model_id}: {input_price_str}, using 0")
                    input_price = 0
                    
                try:
                    output_price = float(output_price_str) if output_price_str else 0
                except ValueError:
                    logger.warning(f"Invalid output price format for {model_id}: {output_price_str}, using 0")
                    output_price = 0
                
                # Check if model has multimodal capabilities from architecture
                architecture = model.get('architecture', {})
                is_multimodal = False
                
                if architecture:
                    input_modalities = architecture.get('input_modalities', [])
                    is_multimodal = len(input_modalities) > 1 or 'image' in input_modalities
                
                # Calculate per million tokens pricing for easier display/calculation
                input_price_million = input_price * 1000000
                output_price_million = output_price * 1000000
                
                # Apply markup
                marked_up_input = input_price_million * markup_factor
                marked_up_output = output_price_million * markup_factor
                
                # Calculate cost band based on the higher of input and output price
                max_price = max(marked_up_input, marked_up_output)
                
                # Determine the cost band
                cost_band = ""
                if max_price >= 100.0:
                    cost_band = "$$$$"
                elif max_price >= 10.0:
                    cost_band = "$$$"
                elif max_price >= 1.0:
                    cost_band = "$$"
                elif max_price >= 0.01:
                    cost_band = "$"
                else:
                    cost_band = ""  # Free or nearly free models get no cost band
                    
                # Get the model name and description
                model_name = model.get('name', model_id.split('/')[-1])
                description = model.get('description', '')
                
                # Get the context length
                context_length = model.get('context_length', None)
                if not isinstance(context_length, int) and context_length is not None:
                    try:
                        context_length = int(context_length)
                    except (ValueError, TypeError):
                        context_length = None
                
                try:
                    # Try to get existing model from the database
                    db_model = db.session.get(OpenRouterModel, model_id)
                    
                    if db_model:
                        # Update existing model
                        db_model.name = model_name
                        db_model.description = description
                        db_model.context_length = context_length
                        db_model.input_price_usd_million = marked_up_input
                        db_model.output_price_usd_million = marked_up_output
                        db_model.is_multimodal = is_multimodal
                        db_model.cost_band = cost_band
                        
                        # Update the new fields
                        db_model.is_free = marked_up_input < 0.01 or ':free' in model_id.lower()
                        
                        model_name_lower = model_name.lower() if model_name else ''
                        description_lower = description.lower() if description else ''
                        db_model.supports_reasoning = any(keyword in model_id.lower() or keyword in model_name_lower or keyword in description_lower 
                                                     for keyword in ['reasoning', 'opus', 'o1', 'o3', 'gpt-4', 'claude-3'])
                        
                        # Update timestamps
                        db_model.updated_at = datetime.utcnow()
                        db_model.last_fetched_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        # Check for free models based on price or special tags
                        is_free = marked_up_input < 0.01 or ':free' in model_id.lower()
                        
                        # Check for reasoning support based on model ID
                        model_name_lower = model_name.lower() if model_name else ''
                        description_lower = description.lower() if description else ''
                        supports_reasoning = any(keyword in model_id.lower() or keyword in model_name_lower or keyword in description_lower 
                                            for keyword in ['reasoning', 'opus', 'o1', 'o3', 'gpt-4', 'claude-3'])
                        
                        # Create new model
                        new_model = OpenRouterModel(
                            model_id=model_id,
                            name=model_name,
                            description=description,
                            context_length=context_length,
                            input_price_usd_million=marked_up_input,
                            output_price_usd_million=marked_up_output,
                            is_multimodal=is_multimodal,
                            is_free=is_free,
                            supports_reasoning=supports_reasoning,
                            cost_band=cost_band,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                            last_fetched_at=datetime.utcnow()
                        )
                        db.session.add(new_model)
                        new_count += 1
                        
                except Exception as model_error:
                    logger.error(f"Error updating model {model_id} in database: {model_error}")
                    continue
            
            # Commit all changes in one transaction
            try:
                db.session.commit()
                logger.info(f"Database updated: {updated_count} models updated, {new_count} new models added")
                return True
            except SQLAlchemyError as e:
                logger.error(f"Database error storing models: {e}")
                db.session.rollback()
                return False
                
    except requests.RequestException as req_err:
        logger.error(f"Request error fetching model prices: {req_err}")
        return False
    except Exception as e:
        logger.error(f"Error fetching or processing model prices: {e}")
        return False

def update_schema():
    """Update the OpenRouterModel table schema to add new fields"""
    with app_context() as db:
        try:
            from models import OpenRouterModel
            
            # Check if the table exists
            if not check_table_exists():
                logger.info("Table doesn't exist yet, skipping schema update")
                return True
                
            # Check for missing columns
            columns_to_check = {
                'is_free': "ALTER TABLE open_router_model ADD COLUMN is_free BOOLEAN DEFAULT FALSE",
                'supports_reasoning': "ALTER TABLE open_router_model ADD COLUMN supports_reasoning BOOLEAN DEFAULT FALSE",
                'created_at': "ALTER TABLE open_router_model ADD COLUMN created_at TIMESTAMP DEFAULT NOW()",
                'updated_at': "ALTER TABLE open_router_model ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()"
            }
            
            # Execute each ALTER TABLE statement if the column doesn't exist
            for column, alter_statement in columns_to_check.items():
                try:
                    # Check if column exists
                    result = db.session.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='open_router_model' AND column_name='{column}'").fetchone()
                    
                    if not result:
                        logger.info(f"Adding column {column} to open_router_model table")
                        db.session.execute(alter_statement)
                        db.session.commit()
                        logger.info(f"Column {column} added successfully")
                    else:
                        logger.info(f"Column {column} already exists")
                        
                except Exception as column_error:
                    logger.error(f"Error adding column {column}: {column_error}")
                    db.session.rollback()
                    # Continue with other columns even if one fails
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating schema: {e}")
            return False

def run_migrations():
    """Run all migrations for OpenRouter model persistence"""
    logger.info("Starting OpenRouter model database migrations...")
    
    # First create the tables if they don't exist
    tables_created = create_tables()
    if not tables_created:
        logger.error("Failed to create tables, aborting migrations")
        return False
    
    # Update schema to add new columns if needed
    schema_updated = update_schema()
    if not schema_updated:
        logger.warning("Schema update had issues, continuing with caution")
    
    # Then fetch and populate models
    models_populated = fetch_and_populate_models()
    if not models_populated:
        logger.warning("Failed to populate models from API, table exists but may be empty")
        # Continue anyway, as this is not a critical error
    
    logger.info("OpenRouter model database migrations completed successfully")
    return True

if __name__ == "__main__":
    success = run_migrations()
    if success:
        logger.info("Migrations completed successfully")
        sys.exit(0)
    else:
        logger.error("Migrations failed")
        sys.exit(1)