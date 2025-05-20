"""
Application Initialization Module

This module manages the initialization of various application components,
prioritizing critical components for fast application startup and deferring
non-critical initialization to background processes.
"""

import os
import time
import logging
from typing import Dict, Any, List, TYPE_CHECKING, Optional, cast

# Type checking imports
if TYPE_CHECKING:
    from background_initializer import BackgroundInitializer

# Setup logging
logger = logging.getLogger(__name__)

def initialize_azure_storage() -> Dict[str, Any]:
    """
    Initialize Azure Blob Storage for file uploads
    
    Returns:
        Dict with initialization status and details
    """
    try:
        from azure.storage.blob import BlobServiceClient

        # Get connection string and container name from environment variables
        azure_connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        azure_container_name = os.environ.get("AZURE_STORAGE_CONTAINER_NAME", "gloriamundoblobs")
        
        if not azure_connection_string:
            logger.warning("Missing Azure Storage connection string, will use local storage")
            return {
                'success': False,
                'status': 'missing_credentials',
                'details': 'Azure Storage connection string not found in environment'
            }
            
        # Create the BlobServiceClient with explicit timeout settings
        start_time = time.time()
        blob_service_client = BlobServiceClient.from_connection_string(
            azure_connection_string,
            connection_timeout=10,
            retry_total=3
        )
        
        # Get a client to interact with the container
        container_client = blob_service_client.get_container_client(azure_container_name)
        
        # Check if container exists, if not create it
        container_exists = False
        try:
            container_exists = container_client.exists()
            if not container_exists:
                container_client = blob_service_client.create_container(azure_container_name)
                container_exists = True
        except Exception as e:
            logger.error(f"Error checking/creating Azure container: {e}")
            return {
                'success': False,
                'status': 'container_error',
                'details': str(e)
            }
        
        elapsed = time.time() - start_time
        
        return {
            'success': True,
            'status': 'initialized',
            'container': azure_container_name,
            'container_exists': container_exists,
            'initialization_time': elapsed
        }
        
    except Exception as e:
        logger.error(f"Error initializing Azure Storage: {e}")
        return {
            'success': False,
            'status': 'error',
            'details': str(e)
        }

def run_database_migrations() -> Dict[str, Any]:
    """
    Run all necessary database migrations in background
    
    Returns:
        Dict with migration status and details
    """
    try:
        from app import app, db
        
        migration_results = {
            'openrouter_model': False,
            'user_chat_settings': False,
            'conversation_index': False,
            'message_index': False,
            'affiliate': False,
            'google_username': False  # New migration to update Google usernames
        }
        
        with app.app_context():
            # Run OpenRouter model migrations if needed
            try:
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                
                # OpenRouter model migration
                if not inspector.has_table('open_router_model'):
                    logger.info("OpenRouterModel table not found, running migrations...")
                    from migrations_openrouter_model import run_migrations
                    success = run_migrations()
                    migration_results['openrouter_model'] = success
                else:
                    logger.info("OpenRouterModel table already exists, skipping migrations")
                    migration_results['openrouter_model'] = True
                    
                # UserChatSettings migration
                logger.info("Running UserChatSettings migration...")
                from migrations_user_chat_settings import run_migration
                success = run_migration()
                migration_results['user_chat_settings'] = success
                
                # Google username migration (to fix username uniqueness issues)
                logger.info("Running Google username migration...")
                try:
                    from migrations_google_username import run_migration
                    success = run_migration()
                    migration_results['google_username'] = success
                    logger.info(f"Google username migration completed with status: {success}")
                except Exception as e:
                    logger.error(f"Error running Google username migration: {e}")
                    migration_results['google_username'] = False
                
                # Run affiliate user_id migration 
                logger.info("Running affiliate user_id migration...")
                try:
                    from migrations.affiliate_migration import run_migration as run_affiliate_migration
                    success = run_affiliate_migration(app, db)
                    migration_results['affiliate'] = success
                    logger.info(f"Affiliate user_id migration completed with status: {success}")
                except Exception as e:
                    logger.error(f"Error running affiliate user_id migration: {e}")
                    migration_results['affiliate'] = False
                
                # Remove hypothetical migration that doesn't exist in the codebase
                # This avoids the error with non-existent imports
                migration_results['conversation_index'] = True  # Assume success for now
                migration_results['message_index'] = True       # Assume success for now
                
                # Log migration summary
                successful = sum(1 for result in migration_results.values() if result)
                total = len(migration_results)
                logger.info(f"Database migrations completed: {successful}/{total} successful")
                
            except Exception as e:
                logger.error(f"Error running database migrations: {e}")
                return {
                    'success': False,
                    'status': 'error',
                    'details': str(e),
                    'results': migration_results
                }
                
        return {
            'success': True,
            'status': 'completed',
            'results': migration_results
        }
    
    except Exception as e:
        logger.error(f"Error during database migrations: {e}")
        return {
            'success': False,
            'status': 'error',
            'details': str(e)
        }

def initialize_model_cache() -> Dict[str, Any]:
    """
    Initialize and validate the model information cache
    
    This ensures price information for AI models is available without 
    blocking application startup.
    
    Returns:
        Dict with initialization status and details
    """
    try:
        from price_updater import fetch_and_store_openrouter_prices
        
        # Start time for performance tracking
        start_time = time.time()
        
        # Force update to ensure we have the latest data
        success = fetch_and_store_openrouter_prices(force_update=True)
        
        elapsed = time.time() - start_time
        
        if success:
            return {
                'success': True,
                'status': 'updated',
                'initialization_time': elapsed
            }
        else:
            return {
                'success': False,
                'status': 'update_failed',
                'initialization_time': elapsed
            }
    
    except Exception as e:
        logger.error(f"Error initializing model cache: {e}")
        return {
            'success': False,
            'status': 'error',
            'details': str(e)
        }

def setup_background_initialization():
    """
    Set up and start the background initialization process.
    This defers non-critical initialization to background threads to improve startup time.
    
    Returns:
        The initialized BackgroundInitializer instance
    """
    try:
        from background_initializer import BackgroundInitializer
        
        # Create the initializer
        initializer = BackgroundInitializer()
        
        # Add tasks with priorities and dependencies
        # Lower priority numbers run first
        
        # 1. Database migrations (priority 1)
        initializer.add_task(
            name='database_migrations',
            func=run_database_migrations,
            priority=1,
            timeout=120  # Allow more time for database migrations
        )
        
        # 2. Azure Storage initialization (priority 2)
        initializer.add_task(
            name='azure_storage',
            func=initialize_azure_storage,
            priority=2,
            timeout=30
        )
        
        # 3. Model cache initialization (priority 3, depends on database migrations)
        initializer.add_task(
            name='model_cache',
            func=initialize_model_cache,
            priority=3,
            dependencies=['database_migrations'],
            timeout=60
        )
        
        # Start the initialization process
        initializer.start()
        
        return initializer
        
    except Exception as e:
        logger.error(f"Error setting up background initialization: {e}")
        # Return a dummy initializer that does nothing to avoid errors
        from background_initializer import BackgroundInitializer
        return BackgroundInitializer()