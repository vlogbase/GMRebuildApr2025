"""
Flask server starter module for running the application
This approach avoids circular imports by keeping a clean import chain
"""

import os
import logging
from flask import Flask
from database import init_app, db
import models  # This imports the models to ensure they're registered with SQLAlchemy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app_server.log'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    # Create the Flask app
    app = Flask(__name__)
    
    # Configure secret key
    secret_key = os.environ.get("SESSION_SECRET")
    if not secret_key:
        logger.warning("SESSION_SECRET environment variable not set. Using default for development.")
        secret_key = "default-dev-secret-key-please-change"
    app.secret_key = secret_key
    
    # Initialize database
    init_app(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Import and register blueprints and routes after app is created
    # This import is deliberately placed here to avoid circular imports
    from routes import register_routes
    register_routes(app)
    
    return app

def run_server():
    """Run the Flask server"""
    app = create_app()
    
    # Determine port
    port = int(os.environ.get("PORT", 5000))
    
    # Run the application
    logger.info(f"Starting Flask application on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)

if __name__ == "__main__":
    run_server()