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

def check_database_health() -> Dict[str, Any]:
    """
    Quick database health check without running migrations.
    Migrations are now handled by deployment scripts, not instance startup.
    
    Returns:
        Dict with database health status
    """
    try:
        from app import app, db
        
        with app.app_context():
            # Simple connectivity test
            from sqlalchemy import text
            with db.engine.connect() as connection:
                connection.execute(text('SELECT 1'))
            
            # Check if critical tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            critical_tables = ['user', 'conversation', 'message']
            missing_tables = []
            
            for table in critical_tables:
                if not inspector.has_table(table):
                    missing_tables.append(table)
            
            if missing_tables:
                return {
                    'success': False,
                    'status': 'missing_tables',
                    'missing_tables': missing_tables,
                    'message': 'Critical tables missing - run deployment migrations'
                }
            
            return {
                'success': True,
                'status': 'healthy',
                'message': 'Database connectivity confirmed'
            }
                
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'success': False,
            'status': 'error',
            'details': str(e),
            'message': 'Database connection failed'
        }

def initialize_price_fetching_with_locks() -> Dict[str, Any]:
    """
    Initialize price fetching using Redis distributed locks for cluster coordination.
    
    This calls the now-Redis-locked fetch_and_store_openrouter_prices() function,
    which ensures only one instance across the cluster performs expensive API calls.
    
    Returns:
        Dict with initialization status and details
    """
    try:
        from price_updater import fetch_and_store_openrouter_prices
        from singleton_background_worker import start_singleton_worker
        
        # Start time for performance tracking
        start_time = time.time()
        
        # Start the singleton worker for scheduled tasks
        logger.info("Starting singleton worker for scheduled tasks...")
        worker = start_singleton_worker()
        
        # Call the Redis-locked price fetching function
        # If another instance is already fetching, this will return quickly
        logger.info("Initializing price data with cluster coordination...")
        price_success = fetch_and_store_openrouter_prices()
        
        elapsed = time.time() - start_time
        
        return {
            'success': True,
            'status': 'initialized',
            'price_fetch_success': price_success,
            'worker_started': worker is not None,
            'initialization_time': elapsed
        }
    
    except Exception as e:
        logger.error(f"Error initializing optimized price fetching: {e}")
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
        
        # 1. Database health check (priority 1)
        initializer.add_task(
            name='database_health_check',
            func=check_database_health,
            priority=1,
            timeout=30  # Quick health check
        )
        
        # 2. Azure Storage initialization (priority 2)
        initializer.add_task(
            name='azure_storage',
            func=initialize_azure_storage,
            priority=2,
            timeout=30
        )
        
        # 3. Initialize optimized price fetching (priority 3, depends on database health)
        # This uses Redis distributed locks for cluster-wide coordination
        initializer.add_task(
            name='optimized_price_init',
            func=initialize_price_fetching_with_locks,
            priority=3,
            dependencies=['database_health_check'],
            timeout=15  # Fast with distributed locks
        )
        
        # Start the initialization process
        initializer.start()
        
        return initializer
        
    except Exception as e:
        logger.error(f"Error setting up background initialization: {e}")
        # Return a dummy initializer that does nothing to avoid errors
        from background_initializer import BackgroundInitializer
        return BackgroundInitializer()