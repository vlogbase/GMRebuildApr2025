"""
Database configuration module for the application.
This module initializes the SQLAlchemy database connection and avoids circular imports.
"""

import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with our base class
db = SQLAlchemy(model_class=Base)

def init_app(app):
    """Initialize the database with the Flask app"""
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 5,  # Conservative pool size
        "max_overflow": 10,  # Allow overflow connections
        "pool_recycle": 1800,  # Recycle connections after 30 minutes
        "pool_pre_ping": True,  # Check connection validity before using from pool
        "pool_timeout": 20,  # Wait up to 20 seconds for a connection from the pool
        "pool_reset_on_return": "commit",  # Reset connections on return to pool
        "connect_args": {
            "sslmode": "require",
            "connect_timeout": 10,
            "application_name": "gloriamundo_chatbot"
        }
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Disable tracking to improve performance
    db.init_app(app)