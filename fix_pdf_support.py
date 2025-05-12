"""
Comprehensive script to fix PDF support in the application.

This script:
1. Runs database migrations to add PDF fields to the Message model
2. Applies app context fixes to prevent "Working outside of application context" errors
3. Tests PDF handling functionality to ensure everything works as expected
"""
import logging
import os
import subprocess
import sys
from importlib import import_module

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pdf_fix.log')
    ]
)

logger = logging.getLogger(__name__)

def check_pdf_fields_in_schema():
    """Check if the Message model already has PDF fields"""
    try:
        from models import Message
        # Create a dummy message to check fields
        msg = Message()
        has_pdf_url = hasattr(msg, 'pdf_url')
        has_pdf_filename = hasattr(msg, 'pdf_filename')
        
        if has_pdf_url and has_pdf_filename:
            logger.info("✅ Message model already has PDF fields")
            return True
        else:
            missing = []
            if not has_pdf_url:
                missing.append("pdf_url")
            if not has_pdf_filename:
                missing.append("pdf_filename")
            logger.info(f"❌ Message model missing PDF fields: {', '.join(missing)}")
            return False
    except Exception as e:
        logger.error(f"Error checking PDF fields: {e}")
        return False

def run_migrations():
    """Run database migrations to add PDF fields to the Message model"""
    try:
        logger.info("Running database migrations for PDF support...")
        
        # Check if migrations_pdf_support.py exists
        if not os.path.exists('migrations_pdf_support.py'):
            logger.error("migrations_pdf_support.py not found. Cannot run migrations.")
            return False
            
        # Import and run migrations
        pdf_migrations = import_module('migrations_pdf_support')
        
        if hasattr(pdf_migrations, 'run_migrations'):
            pdf_migrations.run_migrations()
            logger.info("✅ Successfully ran PDF support migrations")
            return True
        else:
            logger.error("migrations_pdf_support.py does not have run_migrations function")
            return False
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        return False

def fix_app_context():
    """Fix app context issues by copying ensure_app_context.py if needed"""
    try:
        logger.info("Checking/fixing application context handling...")
        
        # Check if ensure_app_context.py already exists
        if os.path.exists('ensure_app_context.py'):
            logger.info("✅ ensure_app_context.py already exists")
        else:
            # Create the file with minimal implementation
            with open('ensure_app_context.py', 'w') as f:
                f.write('''"""
Application context manager for Flask to prevent "outside application context" errors.
"""

import functools
import logging
from contextlib import contextmanager
from flask import current_app, has_app_context

logger = logging.getLogger(__name__)

def get_app():
    """Get the current Flask application."""
    try:
        from app import app
        return app
    except ImportError:
        logger.error("Could not import app")
        return None

@contextmanager
def ensure_app_context():
    """
    Context manager to ensure operations are performed within the Flask application context.
    """
    app = get_app()
    if app is None:
        logger.error("No Flask app available")
        raise RuntimeError("No Flask application available")
        
    if has_app_context():
        # Already in an app context, do nothing
        yield
    else:
        # Create a new app context
        logger.debug("Pushing new application context")
        with app.app_context():
            yield

def with_app_context(func):
    """Decorator to ensure a function runs within a Flask application context."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with ensure_app_context():
            return func(*args, **kwargs)
    return wrapper
''')
            logger.info("✅ Created ensure_app_context.py")

        # Import to test
        try:
            from ensure_app_context import ensure_app_context
            logger.info("✅ ensure_app_context imported successfully")
            return True
        except ImportError as e:
            logger.error(f"Error importing ensure_app_context: {e}")
            return False
    except Exception as e:
        logger.error(f"Error fixing app context: {e}")
        return False

def test_pdf_handling():
    """Test PDF handling functionality"""
    try:
        logger.info("Testing PDF handling functionality...")
        
        # Check if test_pdf_handling.py exists
        if not os.path.exists('test_pdf_handling.py'):
            logger.info("test_pdf_handling.py not found. Skipping tests.")
            return None
            
        # Import and run tests
        import test_pdf_handling
        
        if hasattr(test_pdf_handling, 'run_tests'):
            result = test_pdf_handling.run_tests()
            if result:
                logger.info("✅ PDF handling tests passed")
            else:
                logger.warning("⚠️ Some PDF handling tests failed")
            return result
        else:
            logger.error("test_pdf_handling.py does not have run_tests function")
            return False
    except Exception as e:
        logger.error(f"Error testing PDF handling: {e}")
        return False

def run_all_fixes():
    """Run all PDF support fixes in the correct order"""
    logger.info("=== Starting PDF Support Fix Script ===")
    
    # Step 1: Check if PDF fields already exist in the schema
    schema_has_pdf_fields = check_pdf_fields_in_schema()
    
    # Step 2: Run migrations if needed
    if not schema_has_pdf_fields:
        migrations_success = run_migrations()
        if not migrations_success:
            logger.error("❌ Failed to run migrations. Cannot continue.")
            return False
    
    # Step 3: Fix app context
    context_fix_success = fix_app_context()
    if not context_fix_success:
        logger.error("❌ Failed to fix app context. Cannot continue.")
        return False
    
    # Step 4: Test PDF handling
    test_result = test_pdf_handling()
    
    # Print summary
    logger.info("=== PDF Support Fix Summary ===")
    logger.info(f"Schema has PDF fields: {'✅ Yes' if schema_has_pdf_fields else '✅ Added via migrations'}")
    logger.info(f"App context handling: {'✅ Fixed' if context_fix_success else '❌ Failed'}")
    logger.info(f"PDF handling tests: {'✅ Passed' if test_result == True else '❌ Failed' if test_result == False else '⚠️ Skipped'}")
    
    # Overall result
    if (schema_has_pdf_fields or migrations_success) and context_fix_success:
        logger.info("🎉 PDF support fixes successfully applied!")
        return True
    else:
        logger.error("⚠️ Some PDF support fixes failed.")
        return False

if __name__ == "__main__":
    run_all_fixes()