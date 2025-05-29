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

def start_singleton_background_worker() -> Dict[str, Any]:
    """
    Start the singleton background worker that handles system-wide tasks.
    
    This replaces the old model cache initialization with a proper singleton
    service that coordinates across all instances using Redis distributed locks.
    
    Returns:
        Dict with initialization status and details
    """
    try:
        from singleton_background_worker import start_singleton_worker
        
        # Start time for performance tracking
        start_time = time.time()
        
        # Start the singleton worker
        worker = start_singleton_worker()
        
        elapsed = time.time() - start_time
        
        return {
            'success': True,
            'status': 'started',
            'worker_status': worker.get_status() if worker else {},
            'initialization_time': elapsed
        }
    
    except Exception as e:
        logger.error(f"Error starting singleton background worker: {e}")
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
        
        # 3. Start singleton background worker (priority 3, depends on database health)
        initializer.add_task(
            name='singleton_worker',
            func=start_singleton_background_worker,
            priority=3,
            dependencies=['database_health_check'],
            timeout=30
        )
        
        # Start the initialization process
        initializer.start()
        
        return initializer
        
    except Exception as e:
        logger.error(f"Error setting up background initialization: {e}")
        # Return a dummy initializer that does nothing to avoid errors
        from background_initializer import BackgroundInitializer
        return BackgroundInitializer()