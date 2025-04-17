# --- Simplified main.py with Gevent monkey patching ---
from gevent import monkey
monkey.patch_all()  # IMPORTANT: This must be first, before any other imports!

import logging
from app import app # Import the Flask app object directly
from app import db  # Import db from the app module

# Import models to ensure they're registered with the ORM
import models

logger = logging.getLogger(__name__) # Use logger defined in app.py if desired

# Initialize database tables and run migrations within app context
with app.app_context():
    logger.info("Creating database tables if they don't exist...")
    try:
        db.create_all()
        logger.info("db.create_all() completed.")
    except Exception as e:
        logger.exception("Error during db.create_all()")

    # Run database migrations (optional, based on your setup)
    try:
        from migrations import migrate_database
        logger.info("Running database migrations...")
        migrate_database()
        logger.info("Database migrations completed.")
    except ImportError:
         logger.info("migrations.py not found or migrate_database function missing, skipping.")
    except Exception as e:
        logger.exception("Error running migrations")
        
    # Run image URL migration for multimodal support
    try:
        from migrations_image_url import migrate_database as migrate_image_url
        logger.info("Running image URL migration for multimodal support...")
        migrate_image_url()
        logger.info("Image URL migration completed.")
    except ImportError:
         logger.info("migrations_image_url.py not found, skipping.")
    except Exception as e:
        logger.exception("Error running image URL migration")

# NOTE: No WsgiToAsgi wrapper here. Uvicorn running 'main:app' 
# will load the standard Flask app object directly.

# The block below is only executed when running 'python main.py' directly
# It is NOT used when running with Uvicorn/Gunicorn
if __name__ == '__main__':
    logger.warning("Running Flask app directly using app.run() (for development only)")
    # To test async locally, run 'uvicorn main:app --reload' in the shell
    app.run(host='0.0.0.0', port=5000, debug=True) 
# --- End of Simplified main.py ---