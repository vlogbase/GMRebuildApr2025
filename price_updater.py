"""
Price Updater Module for GloriaMundo Chatbot

This module handles background fetching and caching of OpenRouter model prices,
ensuring model information is stored in the database for reliability.

This module can be run as a standalone script:
    python price_updater.py

Or its functions can be imported and used by app.py:
    from price_updater import fetch_and_store_openrouter_prices, model_prices_cache
"""

import os
import time
import logging
import requests
import sys
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from flask import Flask, current_app
from contextlib import contextmanager

# Set up logging - MUST BE BEFORE ANY OTHER CODE USES LOGGER
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize a cache dict to store model prices (kept for backward compatibility)
model_prices_cache = {
    'prices': {},
    'last_updated': None
}

def get_db(app_instance=None):
    """
    Get the database object.
    
    Args:
        app_instance: Optional Flask app instance. If provided, gets db from this app.
                     If None, tries to get db from current_app.
    
    Returns:
        SQLAlchemy db instance or None if not available
    """
    try:
        if app_instance:
            # Use provided app instance
            return app_instance.extensions['sqlalchemy'].db
        else:
            # Try to get from current Flask app context
            from flask import current_app
            return current_app.extensions['sqlalchemy'].db
    except (RuntimeError, KeyError, ImportError) as e:
        logger.error(f"Failed to get db: {e}")
        return None

@contextmanager
def get_app_context(app_instance=None):
    """
    Context manager for Flask application context.
    If app_instance is provided, uses its context.
    Otherwise, returns a dummy context manager.
    
    Args:
        app_instance: Optional Flask app instance
        
    Yields:
        The application context
    """
    if app_instance:
        with app_instance.app_context() as ctx:
            yield ctx
    else:
        # Dummy context manager that does nothing
        class DummyContext:
            def __enter__(self):
                return None
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                return False
                
        with DummyContext() as dummy:
            yield dummy

def fetch_and_store_openrouter_prices(app_instance=None, db_instance=None) -> bool:
    """
    Fetch current model prices from OpenRouter API and store them in the database.
    
    This function:
    1. Fetches models from the OpenRouter API
    2. Stores them in the database using the OpenRouterModel model
    3. Also updates the legacy cache for backward compatibility
    
    Args:
        app_instance: Optional Flask app instance for context management
        db_instance: Optional SQLAlchemy db instance
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Mark the start time for performance tracking
    start_time = time.time()
    logger.info("fetch_and_store_openrouter_prices started")
    
    try:
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
        logger.info("Fetching model prices from OpenRouter API...")
        
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
        logger.info(f"Received data for {data_count} models from OpenRouter API")
        
        # Process model data to extract pricing
        prices = {}
        markup_factor = 2.0  # Our markup for pricing
        
        # Process models for OPENROUTER_MODELS_INFO and populate it
        processed_models = []
        
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
            supports_pdf = False
            
            if architecture:
                input_modalities = architecture.get('input_modalities', [])
                is_multimodal = len(input_modalities) > 1 or 'image' in input_modalities
                # Check for PDF support (models that can handle files/PDFs directly)
                supports_pdf = 'file' in input_modalities
            
            # Apply our markup and store in the cache
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
            
            prices[model_id] = {
                'input_price': marked_up_input,  # Price per million tokens with markup
                'output_price': marked_up_output,  # Price per million tokens with markup
                'raw_input_price': input_price_million,  # Price per million tokens without markup
                'raw_output_price': output_price_million,  # Price per million tokens without markup
                'context_length': model.get('context_length', 'Unknown'),
                'is_multimodal': is_multimodal or model.get('is_multimodal', False),
                'supports_pdf': supports_pdf,
                'model_name': model.get('name', model_id.split('/')[-1]),
                'cost_band': cost_band  # Add cost band indicator
            }
            
            # Also add the specific properties needed for OPENROUTER_MODELS_INFO
            model_name = model.get('name', '').lower()
            model_description = model.get('description', '').lower()
            model_id_lower = model_id.lower()
            
            # Add the classification properties needed by app.py
            model['is_free'] = ':free' in model_id_lower or input_price == 0.0
            model['is_multimodal'] = is_multimodal or any(keyword in model_id_lower or keyword in model_name or keyword in model_description 
                                    for keyword in ['vision', 'image', 'multi', 'gpt-4o'])
            model['is_perplexity'] = 'perplexity/' in model_id_lower
            model['is_reasoning'] = any(keyword in model_id_lower or keyword in model_name or keyword in model_description 
                                    for keyword in ['reasoning', 'opus', 'o1', 'o3'])
            
            # Add to processed models
            processed_models.append(model)
        
        # Update the cache with the new prices (kept for backward compatibility)
        model_prices_cache['prices'] = prices
        model_prices_cache['last_updated'] = datetime.now().isoformat()
        
        # Store models in the database (This is the new primary storage method)
        db_success = False

        # Import here to avoid circular imports
        from models import OpenRouterModel
        
        # Determine which database and app objects to use
        db = db_instance
        app = app_instance
        
        # If no db was provided directly, try to get it
        if db is None:
            db = get_db(app)
        
        if db is None:
            logger.error("Cannot store models in database: db is None or not accessible")
            return False
        
        # Use application context for all database operations
        with get_app_context(app):
            updated_count = 0
            new_count = 0
            
            # First, mark all models as inactive - we'll re-activate the ones we find in the API response
            try:
                # Mark all existing models as inactive before updating
                OpenRouterModel.query.update({OpenRouterModel.model_is_active: False})
                db.session.flush()
                logger.info("Marked all existing models as inactive")
            except Exception as e:
                logger.error(f"Error marking models as inactive: {e}")
            
            # Use a single database session for all operations
            for model_id, model_data in prices.items():
                try:
                    # Try to get existing model from the database
                    db_model = db.session.get(OpenRouterModel, model_id)
                    
                    if db_model:
                        # Update existing model
                        db_model.name = model_data['model_name']
                        
                        # Find the original model object to get description
                        original_model = next((m for m in models_data.get('data', []) if m.get('id') == model_id), {})
                        db_model.description = original_model.get('description', '')
                        
                        # Update pricing and other details
                        db_model.context_length = model_data['context_length'] if isinstance(model_data['context_length'], int) else None
                        db_model.input_price_usd_million = model_data['input_price']
                        db_model.output_price_usd_million = model_data['output_price']
                        db_model.is_multimodal = model_data['is_multimodal']
                        db_model.supports_pdf = model_data['supports_pdf']
                        db_model.cost_band = model_data['cost_band']
                        
                        # Update additional fields
                        # Check for free models based on price or special tags
                        db_model.is_free = model_data['input_price'] < 0.01 or ':free' in model_id.lower()
                        
                        # Check for reasoning support based on model ID and description
                        model_name = original_model.get('name', '').lower()
                        model_description = original_model.get('description', '').lower()
                        db_model.supports_reasoning = any(keyword in model_id.lower() or keyword in model_name or keyword in model_description 
                                                     for keyword in ['reasoning', 'opus', 'o1', 'o3', 'gpt-4', 'claude-3'])
                        
                        # Since we found this model in the API response, mark it as active
                        db_model.model_is_active = True
                        
                        # Update timestamps
                        db_model.last_fetched_at = datetime.utcnow()
                        db_model.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        # Create new model
                        original_model = next((m for m in models_data.get('data', []) if m.get('id') == model_id), {})
                        context_length = model_data['context_length']
                        if not isinstance(context_length, int):
                            try:
                                context_length = int(context_length)
                            except (ValueError, TypeError):
                                context_length = None
                        
                        # Check for free models based on price or special tags
                        is_free = model_data['input_price'] < 0.01 or ':free' in model_id.lower()
                        
                        # Check for reasoning support based on model ID and description
                        model_name = original_model.get('name', '').lower()
                        model_description = original_model.get('description', '').lower()
                        supports_reasoning = any(keyword in model_id.lower() or keyword in model_name or keyword in model_description 
                                            for keyword in ['reasoning', 'opus', 'o1', 'o3', 'gpt-4', 'claude-3'])
                        
                        # Create a new model instance
                        new_model = OpenRouterModel(
                            model_id=model_id,
                            name=model_data['model_name'],
                            description=original_model.get('description', ''),
                            context_length=context_length,
                            input_price_usd_million=model_data['input_price'],
                            output_price_usd_million=model_data['output_price'],
                            is_multimodal=model_data['is_multimodal'],
                            supports_pdf=model_data['supports_pdf'],
                            cost_band=model_data['cost_band'],
                            is_free=is_free,
                            supports_reasoning=supports_reasoning,
                            model_is_active=True,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                            last_fetched_at=datetime.utcnow()
                        )
                        
                        # Add to database
                        db.session.add(new_model)
                        new_count += 1
                except Exception as model_error:
                    logger.error(f"Error processing model {model_id}: {model_error}")
            
            # Commit all changes
            try:
                db.session.commit()
                db_success = True
                logger.info(f"Database updated: {updated_count} models updated, {new_count} new models added")
            except Exception as commit_error:
                logger.error(f"Error committing changes to database: {commit_error}")
                try:
                    db.session.rollback()
                except Exception:
                    logger.error("Error during rollback")
                db_success = False
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        logger.info(f"fetch_and_store_openrouter_prices completed in {elapsed_time:.2f} seconds")
        
        # Return True if either the cache update or database update was successful
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching models from OpenRouter API: {e}")
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        logger.info(f"fetch_and_store_openrouter_prices failed after {elapsed_time:.2f} seconds")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in fetch_and_store_openrouter_prices: {e}")
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        logger.info(f"fetch_and_store_openrouter_prices failed after {elapsed_time:.2f} seconds")
        return False

def should_refresh_prices():
    """
    Check if prices need to be refreshed.
    Returns True if prices are older than 24 hours or have not been fetched yet.
    """
    if model_prices_cache.get('last_updated') is None:
        return True
    
    try:
        last_updated = datetime.fromisoformat(model_prices_cache['last_updated'])
        now = datetime.now()
        elapsed = now - last_updated
        return elapsed > timedelta(hours=24)
    except (ValueError, TypeError):
        return True

def create_app():
    """
    Create a minimal Flask application for standalone execution.
    This is only used when this script is run directly.
    """
    app = Flask(__name__)
    
    # Configure the database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///openrouter_models.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Import and initialize the database
    from flask_sqlalchemy import SQLAlchemy
    from sqlalchemy.orm import DeclarativeBase
    
    class Base(DeclarativeBase):
        pass
    
    db = SQLAlchemy(model_class=Base)
    db.init_app(app)
    
    return app, db

if __name__ == "__main__":
    """
    Standalone execution mode.
    When run directly, this script creates its own Flask app and DB connection.
    """
    logger.info("Starting price_updater.py in standalone mode")
    
    # Check if we have the required environment variables
    if not os.environ.get('DATABASE_URL'):
        logger.warning("DATABASE_URL environment variable not set. Using SQLite by default.")
    
    if not os.environ.get('OPENROUTER_API_KEY'):
        logger.error("OPENROUTER_API_KEY environment variable not set. Cannot fetch prices.")
        sys.exit(1)
    
    # Create a minimal Flask app for this execution
    app, db = create_app()
    
    # Create tables if they don't exist
    with app.app_context():
        # Import models here to avoid circular imports
        try:
            from models import OpenRouterModel
            db.create_all()
            
            # Now fetch and store prices using this app context
            success = fetch_and_store_openrouter_prices(app_instance=app, db_instance=db)
            
            if success:
                logger.info("Successfully updated model prices")
                sys.exit(0)
            else:
                logger.error("Failed to update model prices")
                sys.exit(1)
        except ImportError as e:
            logger.error(f"Error importing models: {e}")
            logger.error("If running in standalone mode, ensure models.py exists and contains OpenRouterModel")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error in standalone execution: {e}")
            sys.exit(1)