"""
Run all migrations and fixes for PDF support
"""
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migrations():
    """
    Run database migrations to add PDF support
    """
    try:
        # Run the migration script
        logger.info("Running database migrations for PDF support")
        
        # Import and run the migration
        import migrations_pdf_support
        result = migrations_pdf_support.run_migrations()
        
        if not result:
            logger.error("PDF support migrations failed")
            return False
            
        logger.info("PDF support migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error in database migrations: {e}")
        logger.exception("Migration exception:")
        return False

def fix_application_context():
    """
    Fix Flask application context issues
    """
    try:
        # Run the app context fix
        logger.info("Fixing application context")
        
        # Import and run the fix
        import fix_app_context
        result = fix_app_context.fix_app_context()
        
        if not result:
            logger.error("Application context fix failed")
            return False
            
        logger.info("Application context fix completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error in application context fix: {e}")
        logger.exception("Fix exception:")
        return False

def run_updates():
    """
    Run all updates needed for PDF support
    """
    success = True
    
    # Run database migrations
    if not run_migrations():
        success = False
        logger.warning("PDF support migrations had issues, continuing with other updates")
    
    # Fix application context
    if not fix_application_context():
        success = False
        logger.warning("Application context fix had issues")
    
    if success:
        logger.info("All PDF support updates completed successfully!")
    else:
        logger.warning("PDF support updates had some issues, check the logs for details")
    
    return success

if __name__ == "__main__":
    success = run_updates()
    if success:
        print("✅ PDF support updates completed successfully")
        sys.exit(0)
    else:
        print("⚠️ PDF support updates completed with some issues, check the logs")
        sys.exit(1)