"""
Database initialization for GloriaMundo application
"""
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Create the base model class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the base model
db = SQLAlchemy(model_class=Base)

def init_db(app):
    """
    Initialize the database with the Flask app
    
    Args:
        app: Flask application instance
    """
    # Configure the database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Initialize the app with the extension
    db.init_app(app)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()