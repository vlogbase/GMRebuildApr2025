"""
Main module for GloriaMundo application

This file serves as the primary entry point for the application when deployed.
It initializes the Flask app and all required components in the correct order.
"""
# Monkey patching needs to happen at the very top
from gevent import monkey
monkey.patch_all()

import os
import logging
import sys
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "developmentsecretkey")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database connection
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize database
from database import db
db.init_app(app)

# Initialize LoginManager for user authentication
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Import models after initializing db
with app.app_context():
    import models  # This imports all models
    from price_updater import fetch_and_store_openrouter_prices
    db.create_all()  # Create tables based on models
    
    # Run any necessary migrations
    try:
        # Only attempt migrations when running in production
        if not app.debug or os.environ.get('FORCE_MIGRATIONS', 'false').lower() == 'true':
            from migrations_openrouter_model import run_migrations
            success = run_migrations()
            if success:
                logger.info("OpenRouter model migrations completed successfully")
            else:
                logger.warning("OpenRouter model migrations failed, model data may not be available")
    except Exception as e:
        logger.exception(f"Error running migrations: {e}")
        # Continue anyway as this is not critical

# Initialize the document processor if RAG is enabled
document_processor = None
ENABLE_RAG = os.environ.get('ENABLE_RAG', 'false').lower() == 'true'
if ENABLE_RAG:
    try:
        # Import the DocumentProcessor class
        # We use a conditional import to avoid errors if the module is missing
        import sys
        import importlib.util
        
        # Check if document_processor.py exists before trying to import it
        doc_processor_spec = importlib.util.find_spec('document_processor')
        if doc_processor_spec is not None:
            # Import the module
            from document_processor import DocumentProcessor
            # Initialize the document processor
            document_processor = DocumentProcessor()
            logger.info("Document processor initialized successfully")
        else:
            logger.warning("document_processor.py module not found, disabling RAG")
            ENABLE_RAG = False
    except Exception as e:
        logger.exception(f"Failed to initialize document processor: {e}")
        ENABLE_RAG = False

# Import and register blueprints
from fallback_api import init_fallback_api
init_fallback_api(app)

# Import and set up routes after all initialization is complete
import routes

# This allows gunicorn to find the app instance via 'main:app'
if __name__ == "__main__":
    # Run the app directly if this file is executed
    app.run(host='0.0.0.0', port=5000, debug=True)