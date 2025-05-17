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
        "pool_size": 10,  # Increased from default of 5
        "max_overflow": 20,  # Allow up to 20 connections to be created beyond pool_size
        "pool_recycle": 300,  # Recycle connections after 5 minutes
        "pool_pre_ping": True,  # Check connection validity before using from pool
        "pool_timeout": 30,  # Wait up to 30 seconds for a connection from the pool
        "pool_use_lifo": True,  # Last in, first out for better performance with short requests
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Disable tracking to improve performance
    db.init_app(app)