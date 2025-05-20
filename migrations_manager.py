"""
Migrations Manager

This module handles running database migrations in the correct order during application startup.
"""

import logging
import importlib
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of migration modules to run in order
MIGRATION_MODULES = [
    'migrations_google_username',  # Convert Google usernames to email format
]

def run_migrations():
    """Run all pending migrations in order"""
    logger.info("Starting migrations manager...")
    
    for module_name in MIGRATION_MODULES:
        try:
            # Import the module dynamically
            logger.info(f"Loading migration module: {module_name}")
            migration_module = importlib.import_module(module_name)
            
            # Check if the module has a run_migration function
            if hasattr(migration_module, 'run_migration'):
                logger.info(f"Running migration: {module_name}")
                start_time = datetime.now()
                
                # Run the migration
                success = migration_module.run_migration()
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                if success:
                    logger.info(f"Migration {module_name} completed successfully in {duration:.2f} seconds")
                else:
                    logger.error(f"Migration {module_name} failed after {duration:.2f} seconds")
            else:
                logger.warning(f"Migration module {module_name} does not have a run_migration function")
                
        except ImportError as e:
            logger.warning(f"Could not import migration module {module_name}: {e}")
        except SQLAlchemyError as e:
            logger.error(f"Database error during migration {module_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during migration {module_name}: {e}")
    
    logger.info("Migrations manager completed")
    
if __name__ == "__main__":
    # Run migrations directly if this script is executed
    run_migrations()