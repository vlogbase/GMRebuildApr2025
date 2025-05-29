"""
Price Updater Module for GloriaMundo Chatbot

This module handles background fetching and caching of OpenRouter model prices,
ensuring model information is stored in the database for reliability.
"""

import os
import time
import logging
import threading
import requests
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

# Import from database to avoid circular references
from database import db
from models import OpenRouterModel
from flask import current_app

# Set up logging with more details for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialize a cache dict to store model prices (kept for backward compatibility)
model_prices_cache = {
    'prices': {},
    'last_updated': None
}

def should_update_prices() -> bool:
    """
    Check if we should update prices based on the last update time.
    Only fetch new prices if it's been at least 3 hours since the last update.
    
    This function now utilizes the startup cache for faster performance during initialization.
    
    Returns:
        bool: True if we should update prices, False otherwise
    """
    try:
        # First check the startup cache for faster startup
        try:
            from startup_cache import startup_cache
            
            # Check if model prices are in cache and still fresh (less than 3 hours old)
            if not startup_cache.service_needs_update('model_prices', max_age_hours=3.0):
                logger.info("Using cached model price information (less than 3 hours old)")
                return False
                
            logger.info("Model prices cache needs refresh (older than 3 hours)")
        except ImportError:
            # Cache module not available, continue with database check
            logger.debug("Startup cache not available, falling back to database check")
            pass
                
        # Get app context safely without relying on current_app
        try:
            from app import app, db
            from models import OpenRouterModel
            
            # Use app context for database operations and capture in a variable
            # to ensure the context is properly managed
            with app.app_context():
                # Add retry logic for database operations
                max_retries = 3
                retry_count = 0
                last_model = None
                
                while retry_count < max_retries:
                    try:
                        # Get the most recent update timestamp from any active model
                        last_model = OpenRouterModel.query.filter(OpenRouterModel.model_is_active == True).order_by(
                            OpenRouterModel.last_fetched_at.desc()
                        ).first()
                        
                        # If we get here, the query succeeded, break out of retry loop
                        break
                        
                    except (SQLAlchemyError, Exception) as db_error:
                        retry_count += 1
                        logger.warning(f"Database connection error (attempt {retry_count}/{max_retries}): {db_error}")
                        
                        if retry_count >= max_retries:
                            logger.error("Max database retries exceeded. Forcing price update to be safe.")
                            return True
                        
                        # Wait before retrying
                        time.sleep(1)
                        
                        # Try to dispose the connection pool and recreate
                        try:
                            db.engine.dispose()
                            logger.info("Disposed database connection pool for retry")
                        except Exception:
                            pass
                
                # Process the results within the app context
                if last_model and last_model.last_fetched_at:
                    last_update_time = last_model.last_fetched_at
                    now = datetime.utcnow()
                    hours_since_update = (now - last_update_time).total_seconds() / 3600
                    
                    # Store results to use after the app context is closed
                    need_update = hours_since_update >= 3
                    
                    # Update the startup cache with this information
                    try:
                        from startup_cache import startup_cache
                        
                        # Get count within the app context
                        model_count = OpenRouterModel.query.filter(OpenRouterModel.model_is_active == True).count()
                        
                        # Create cache update data
                        cache_data = {
                            'last_db_update': last_update_time.isoformat(),
                            'hours_since_update': hours_since_update,
                            'model_count': model_count
                        }
                        
                        # Update the cache outside of this block
                    except ImportError:
                        cache_data = None
                        
                    # Return from within the app context to ensure proper closure
                    if hours_since_update < 3:
                        logger.info(f"Skipping price update - last update was {hours_since_update:.1f} hours ago")
                        
                        # Update the cache if we have data
                        if cache_data:
                            try:
                                from startup_cache import startup_cache
                                startup_cache.update_service_data('model_prices', cache_data)
                            except Exception as cache_error:
                                logger.warning(f"Failed to update startup cache: {cache_error}")
                        
                        return False
                        
                    logger.info(f"Updating prices - it's been {hours_since_update:.1f} hours since the last update")
                    
                    # Update the cache if we have data
                    if cache_data:
                        try:
                            from startup_cache import startup_cache
                            startup_cache.update_service_data('model_prices', cache_data)
                        except Exception as cache_error:
                            logger.warning(f"Failed to update startup cache: {cache_error}")
                    
                    return True
                else:
                    # No models in database yet or no timestamp, so we should update
                    logger.info("No existing models with timestamps found - will update prices")
                    return True
        except ImportError as import_error:
            logger.warning(f"Could not import required modules: {import_error}. Will update prices to be safe.")
            return True
            
    except Exception as e:
        logger.warning(f"Error checking last price update time: {e}. Will update prices to be safe.")
        return True

def _populate_redis_pricing_cache():
    """
    Populate Redis cache with current database pricing data.
    This prevents cost band regeneration by ensuring Redis has the latest data.
    """
    try:
        from app import app, db
        from models import OpenRouterModel
        
        with app.app_context():
            # Get all active models from database
            db_models = OpenRouterModel.query.filter_by(model_is_active=True).all()
            
            if not db_models:
                logger.warning("No active models found in database for Redis cache population")
                return
            
            # Build pricing data structure matching the API format
            pricing_data = {}
            models_count = 0
            
            for db_model in db_models:
                model_id = db_model.model_id
                
                # Use stored cost band from database (no regeneration!)
                cost_band = db_model.cost_band or ""
                
                # Get pricing values
                input_price_raw = db_model.input_price_usd_million or 0
                output_price_raw = db_model.output_price_usd_million or 0
                
                # Handle special cases for AutoRouter
                if model_id == "openrouter/auto":
                    input_price_raw = None
                    output_price_raw = None
                    cost_band = "Auto"
                
                # Create pricing data matching API format
                pricing_data[model_id] = {
                    'input_price': input_price_raw,
                    'output_price': output_price_raw,
                    'context_length': str(db_model.context_length) if db_model.context_length else 'N/A',
                    'multimodal': "Yes" if db_model.is_multimodal else "No",
                    'pdfs': "Yes" if db_model.supports_pdf else "No",
                    'model_name': db_model.name or model_id,
                    'model_id': model_id,
                    'cost_band': cost_band,  # Use stored value - no generation!
                    'is_free': db_model.is_free or False,
                    'is_reasoning': db_model.supports_reasoning or False,
                    'elo_score': db_model.elo_score,
                    'source': 'database_cache'
                }
                
                models_count += 1
            
            # Store in Redis cache
            try:
                from api_cache import get_redis_client
                redis_client = get_redis_client()
                
                if redis_client:
                    import json
                    cache_key = 'cache:pricing_table_data'
                    cache_data = json.dumps(pricing_data)
                    
                    # Set with 1 hour TTL (3600 seconds)
                    redis_client.setex(cache_key, 3600, cache_data)
                    logger.info(f"Populated Redis cache with {models_count} models, preventing cost band regeneration")
                else:
                    logger.warning("Redis client not available for cache population")
                    
            except Exception as redis_error:
                logger.error(f"Error storing pricing data in Redis: {redis_error}")
                
    except Exception as e:
        logger.error(f"Error populating Redis pricing cache: {e}")

def fetch_and_store_openrouter_prices(force_update=False) -> bool:
    """
    Fetch current model prices from OpenRouter API and store them in the database.
    
    This function now includes Redis distributed locking to ensure only one instance
    across the entire cluster performs the expensive API fetch and database update.
    
    This function:
    1. Acquires a Redis distributed lock to coordinate across instances
    2. Checks if an update is needed based on time elapsed since last update (unless force_update=True)
    3. Fetches models from the OpenRouter API (only if lock acquired)
    4. Stores them in the database using the OpenRouterModel model
    5. Also updates the legacy cache for backward compatibility
    6. Updates the global OPENROUTER_MODELS_INFO variable for consistency
    7. Releases the Redis lock
    
    Args:
        force_update: If True, bypass the time check and always update
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Import required modules inside function to avoid circular imports
    # and ensure we have access to the app object
    try:
        from app import app, db
    except ImportError as e:
        logger.error(f"Failed to import app modules: {e}")
        return False
    
    # Redis distributed lock setup
    LOCK_KEY = "cluster:price_update_lock"
    LOCK_TTL = 1800  # 30 minutes - enough time for full price update
    redis_client = None
    lock_acquired = False
    worker_id = f"{os.getpid()}_{threading.current_thread().ident}"
    
    try:
        # Get Redis client for distributed locking
        from api_cache import get_redis_client
        redis_client = get_redis_client()
        
        if redis_client:
            # Try to acquire distributed lock using atomic SET NX EX
            lock_acquired = redis_client.set(LOCK_KEY, worker_id, nx=True, ex=LOCK_TTL)
            
            if lock_acquired:
                logger.info(f"✓ Acquired cluster-wide price update lock (worker: {worker_id})")
            else:
                # Check who has the lock
                current_holder = redis_client.get(LOCK_KEY)
                if current_holder:
                    # Handle both bytes and string responses from Redis
                    holder_info = current_holder.decode() if isinstance(current_holder, bytes) else current_holder
                    logger.info(f"⏱️ Price update already running on worker: {holder_info}")
                else:
                    logger.info("⏱️ Price update lock recently released, skipping")
                
                # Check if we should still return True (data is fresh)
                if not force_update and not should_update_prices():
                    logger.info("✓ Prices are fresh, no update needed")
                    return True
                else:
                    logger.info("⚠️ Skipping price update - another instance is handling it")
                    return False
        else:
            logger.warning("⚠️ Redis not available - proceeding without distributed lock")
            # Continue without locking if Redis is unavailable
            
    except Exception as e:
        logger.warning(f"⚠️ Error setting up Redis lock: {e} - proceeding without lock")
        
    try:
        # Check if we should update based on time elapsed
        if not force_update and not should_update_prices():
            logger.info("Skipping price update - prices are recent enough")
            return True
            
        # Mark the start time for performance tracking
        start_time = time.time()
        logger.info("🚀 Cluster-coordinated price update started")
        
        # ELO scores are now managed manually via admin interface - no automatic fetching
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
        # Use query parameters to get ALL models (including ones that might be filtered out by default)
        params = {
            'limit': 1000,  # Get as many models as possible
            'ready': 'all'  # Include all models, not just ready ones
        }
        request_url = 'https://openrouter.ai/api/v1/models'
        logger.debug(f"API Request URL: {request_url} with params: {params}")
        logger.debug(f"Using API key: {masked_key}")
        
        response = requests.get(
            request_url,
            headers=headers,
            params=params,
            timeout=15.0
        )
        
        # Log response status
        logger.debug(f"OpenRouter API response status code: {response.status_code}")
        
        # Check response status
        response.raise_for_status()
        
        # Parse response JSON
        models_data = response.json()
        
        # Log response data with more details
        models = models_data.get('data', [])
        data_count = len(models)
        logger.info(f"Received data for {data_count} models from OpenRouter API")
        
        # Log details of the first few and last few models to understand what we're getting
        if data_count > 0:
            # Log first 3 models
            for i in range(min(3, data_count)):
                model = models[i]
                logger.info(f"First Models - Model {i+1}: {model.get('id')} - {model.get('name')}")
                
            # Log last 3 models
            for i in range(max(0, data_count-3), data_count):
                model = models[i]
                logger.info(f"Last Models - Model {i+1}: {model.get('id')} - {model.get('name')}")
                
            # Check if our target model exists in the data
            target_model_id = "nousresearch/deephermes-3-mistral-24b-preview:free"
            target_model = next((m for m in models if m.get('id') == target_model_id), None)
            if target_model:
                logger.info(f"Target model '{target_model_id}' found in API response")
            else:
                logger.warning(f"Target model '{target_model_id}' NOT found in API response")
        
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
            supports_reasoning = False
            
            if architecture:
                input_modalities = architecture.get('input_modalities', [])
                output_modalities = architecture.get('output_modalities', [])
                modality = architecture.get('modality', '')
                
                # Multimodal: supports images or multiple input types
                is_multimodal = 'image' in input_modalities or len(input_modalities) > 1
                
                # PDF support: explicitly supports file input
                supports_pdf = 'file' in input_modalities
                
                # Reasoning: check if the model supports reasoning parameters
                # This is the most accurate way to detect reasoning models
                supported_parameters = model.get('supported_parameters', [])
                supports_reasoning = 'reasoning' in supported_parameters or 'include_reasoning' in supported_parameters
            
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
            
            # Add the classification properties needed by app.py using actual OpenRouter data
            model['is_free'] = ':free' in model_id_lower or input_price == 0.0
            model['is_multimodal'] = is_multimodal  # Use the architecture-based detection
            model['is_perplexity'] = 'perplexity/' in model_id_lower
            model['supports_pdf'] = supports_pdf  # Use the architecture-based detection
            model['is_reasoning'] = supports_reasoning  # Use the description-based detection for now
            
            # Add to processed models for OPENROUTER_MODELS_INFO
            processed_models.append(model)
        
        # Update the cache with the new prices (kept for backward compatibility)
        model_prices_cache['prices'] = prices
        model_prices_cache['last_updated'] = datetime.now().isoformat()
        
        # Store models in the database (This is the new primary storage method)
        try:
            # Import here to avoid circular imports
            from app import app, db
            from models import OpenRouterModel
            
            # Use a single application context for all database operations
            with app.app_context():
                updated_count = 0
                new_count = 0
                
                # First, mark all models as inactive - we'll re-activate the ones we find in the API response
                try:
                    # Mark all existing models as inactive before updating
                    OpenRouterModel.query.update({OpenRouterModel.model_is_active: False})
                    logger.info("Marked all existing models as inactive")
                except Exception as e:
                    logger.error(f"Error marking models as inactive: {e}")
                
                # Use a single database session for all operations
                for model_id, model_data in prices.items():
                    try:
                        # Try to get existing model from the database
                        db_model = OpenRouterModel.query.get(model_id)
                        
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
                            
                            # ELO scores are now managed manually via admin interface
                            # Don't overwrite existing manually-set ELO scores
                            
                            # Use accurate reasoning support from OpenRouter API supported_parameters
                            original_model = next((m for m in models_data.get('data', []) if m.get('id') == model_id), {})
                            supported_parameters = original_model.get('supported_parameters', [])
                            db_model.supports_reasoning = 'reasoning' in supported_parameters or 'include_reasoning' in supported_parameters
                            
                            # Since we found this model in the API response, mark it as active
                            db_model.model_is_active = True
                            
                            # Update timestamps
                            db_model.last_fetched_at = datetime.utcnow()
                            db_model.updated_at = datetime.utcnow()
                            updated_count += 1
                            
                            # Log updates for specific models we're tracking
                            if model_id in ["nousresearch/deephermes-3-mistral-24b-preview:free"]:
                                logger.info(f"Updated tracked model in database: {model_id}, PDF support: {db_model.supports_pdf}")
                            # Also log some updates for verification
                            elif updated_count <= 3 or updated_count % 50 == 0:
                                logger.info(f"Updated model in database: {model_id}, PDF support: {db_model.supports_pdf}")
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
                            
                            # Use accurate reasoning support from OpenRouter API supported_parameters
                            original_model = next((m for m in models_data.get('data', []) if m.get('id') == model_id), {})
                            supported_parameters = original_model.get('supported_parameters', [])
                            supports_reasoning = 'reasoning' in supported_parameters or 'include_reasoning' in supported_parameters
                            
                            # Ensure cost band is properly set - this prevents models from being filtered out
                            cost_band = model_data['cost_band']
                            if not cost_band or cost_band.strip() == '':
                                # Auto-generate cost band based on pricing
                                input_price = model_data['input_price']
                                if is_free or input_price == 0:
                                    cost_band = "Free"
                                elif input_price < 1.0:
                                    cost_band = "$"
                                elif input_price < 5.0:
                                    cost_band = "$$"
                                else:
                                    cost_band = "$$$"
                                logger.info(f"Auto-generated cost band '{cost_band}' for new model {model_id}")
                            
                            # Create a new model instance
                            new_model = OpenRouterModel()
                            new_model.model_id = model_id
                            new_model.name = model_data['model_name']
                            new_model.description = original_model.get('description', '')
                            new_model.context_length = context_length
                            new_model.input_price_usd_million = model_data['input_price']
                            new_model.output_price_usd_million = model_data['output_price']
                            new_model.is_multimodal = model_data['is_multimodal']
                            new_model.supports_pdf = model_data['supports_pdf']
                            new_model.is_free = is_free
                            new_model.supports_reasoning = supports_reasoning
                            new_model.cost_band = cost_band
                            
                            # ELO scores are managed manually via admin interface for new models
                            new_model.elo_score = None
                            
                            new_model.model_is_active = True
                            new_model.created_at = datetime.utcnow()
                            new_model.updated_at = datetime.utcnow()
                            new_model.last_fetched_at = datetime.utcnow()
                            db.session.add(new_model)
                            new_count += 1
                            
                            # Log newly created models for specific models we're tracking
                            if model_id in ["nousresearch/deephermes-3-mistral-24b-preview:free"]:
                                logger.info(f"Created new database entry for tracked model: {model_id}")
                            # Also log some new models for verification
                            elif new_count <= 3 or new_count % 50 == 0:
                                logger.info(f"Created new database entry for model: {model_id}")
                            
                    except Exception as model_error:
                        logger.error(f"Error updating model {model_id} in database: {model_error}")
                        # Rollback the current transaction to avoid InFailedSqlTransaction errors
                        db.session.rollback()
                        continue
                
                try:
                    # Commit all changes in one transaction
                    db.session.commit()
                    logger.info(f"Database updated: {updated_count} models updated, {new_count} new models added")
                except SQLAlchemyError as commit_error:
                    # If commit fails, rollback and log the error
                    db.session.rollback()
                    logger.error(f"Failed to commit database changes: {commit_error}")
                    # The transaction failed but we don't want to report a complete failure
                    # as we might have had some successful model updates
            
        except ImportError as e:
            logger.error(f"Failed to import database modules: {e}")
            return False
        except SQLAlchemyError as e:
            logger.error(f"Database error storing models: {e}")
            # We're already in an app context from the try block above
            # so we can safely perform the rollback here
            try:
                db.session.rollback()
                logger.info("Successfully rolled back session after SQLAlchemy error")
            except Exception as rollback_error:
                logger.error(f"Error during session rollback: {rollback_error}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error storing models in database: {e}")
            # Similar to above, maintain the current app context
            try:
                db.session.rollback()
                logger.info("Successfully rolled back session after unexpected error")
            except Exception as rollback_error:
                logger.error(f"Error during session rollback: {rollback_error}")
            return False
        
        # CRITICAL FIX: Update Redis cache after database update to prevent cost band regeneration
        try:
            _populate_redis_pricing_cache()
            logger.info("Successfully updated Redis pricing cache after database update")
        except Exception as redis_error:
            logger.warning(f"Failed to update Redis cache after database update: {redis_error}")
            # Don't fail the entire operation if Redis is unavailable
        
        # Log successful completion
        elapsed_time = time.time() - start_time
        logger.info(f"✅ Successfully processed {len(prices)} models in {elapsed_time:.2f} seconds")
        logger.info("🎉 Cluster-coordinated price update completed successfully")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request error fetching model prices: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error fetching or processing model prices: {e}")
        return False
        
    finally:
        # Always release the Redis lock if we acquired it
        if lock_acquired and redis_client:
            try:
                # Use Lua script for atomic check-and-delete to ensure we only delete our own lock
                lua_script = """
                if redis.call("get", KEYS[1]) == ARGV[1] then
                    return redis.call("del", KEYS[1])
                else
                    return 0
                end
                """
                result = redis_client.eval(lua_script, 1, LOCK_KEY, worker_id)
                if result == 1:
                    logger.info(f"🔓 Released cluster-wide price update lock (worker: {worker_id})")
                else:
                    logger.warning(f"⚠️ Could not release price update lock - not owned by this worker")
            except Exception as e:
                logger.error(f"❌ Error releasing Redis lock: {e}")

def get_model_cost(model_id: str) -> dict:
    """
    Get the cost per million tokens and cost band for a specific model.
    This function now primarily uses the database but falls back to cache and then to defaults.
    
    Args:
        model_id (str): The ID of the model
        
    Returns:
        dict: Dictionary containing prompt_cost_per_million, completion_cost_per_million, and cost_band
    """
    try:
        # Import directly to avoid application context issues
        from app import app, db
        from models import OpenRouterModel
        
        # Use a proper app context for all database operations
        with app.app_context():
            # Get model from database
            db_model = OpenRouterModel.query.filter_by(model_id=model_id).first()
                
            if db_model:
                return {
                    'prompt_cost_per_million': db_model.input_price_usd_million,
                    'completion_cost_per_million': db_model.output_price_usd_million,
                    'cost_band': db_model.cost_band or '',
                    'source': 'database'  # For debugging
                }
            
            # If model not found, try to update prices from API
            logger.info(f"Model {model_id} not found in database, attempting to refresh prices")
            
            # Attempt to update the database with fresh data from the API
            # We're already in an app context, so this should work properly
            if fetch_and_store_openrouter_prices(force_update=True):
                # Try database lookup again after the fresh fetch
                db_model = OpenRouterModel.query.filter_by(model_id=model_id).first()
                    
                if db_model:
                    return {
                        'prompt_cost_per_million': db_model.input_price_usd_million,
                        'completion_cost_per_million': db_model.output_price_usd_million,
                        'cost_band': db_model.cost_band or '',
                        'source': 'database_refresh'  # For debugging
                    }
    except Exception as db_error:
        logger.warning(f"Failed to get model cost from database: {db_error}")
    
    # If we still don't have data, use fallback logic
    # Approximate fallback costs based on model name
    model_name = model_id.lower()
    
    # Define prompt and completion costs with fallback values
    prompt_cost = 0.0
    completion_cost = 0.0
    
    if "gpt-4" in model_name:
        prompt_cost = 60.0
        completion_cost = 120.0
        cost_band = "$$$$"
    elif "claude-3" in model_name and "opus" in model_name:
        prompt_cost = 45.0
        completion_cost = 90.0
        cost_band = "$$$$"
    elif "claude-3" in model_name and "sonnet" in model_name:
        prompt_cost = 15.0
        completion_cost = 30.0
        cost_band = "$$$"
    elif "claude-3" in model_name and "haiku" in model_name:
        prompt_cost = 3.0
        completion_cost = 6.0
        cost_band = "$$"
    elif "gemini-1.5" in model_name and "pro" in model_name:
        prompt_cost = 10.0
        completion_cost = 20.0
        cost_band = "$$$"
    elif "gpt-3.5" in model_name:
        prompt_cost = 1.0
        completion_cost = 2.0
        cost_band = "$$"
    else:
        # Default fallback for unknown models
        prompt_cost = 10.0
        completion_cost = 20.0
        cost_band = "$$$"
        
    # Return the fallback data with cost band
    return {
        'prompt_cost_per_million': prompt_cost,
        'completion_cost_per_million': completion_cost,
        'cost_band': cost_band,
        'source': 'fallback'  # For debugging
    }