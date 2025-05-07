#!/usr/bin/env python3
"""
Direct test of OpenRouterModel table and operations.
Bypasses the full app initialization to avoid recursion issues.
"""

import os
import sys
import logging
import requests
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a base class for declarative models
Base = declarative_base()

# Define the OpenRouterModel class
class OpenRouterModel(Base):
    """Model to store OpenRouter model information centrally in the database"""
    __tablename__ = 'open_router_model'
    
    model_id = Column(String(128), primary_key=True)
    name = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    context_length = Column(Float, nullable=True)
    input_price_usd_million = Column(Float, nullable=True)
    output_price_usd_million = Column(Float, nullable=True)
    is_multimodal = Column(Boolean, default=False)
    is_free = Column(Boolean, default=False)
    supports_reasoning = Column(Boolean, default=False)
    cost_band = Column(String(8), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_fetched_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<OpenRouterModel {self.model_id}>"

def add_columns_if_missing(engine, table_name, columns):
    """Add columns to a table if they don't exist already"""
    from sqlalchemy import text
    
    conn = engine.connect()
    for column_name, column_def in columns.items():
        try:
            # Check if column exists
            query = text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}' AND column_name='{column_name}'")
            result = conn.execute(query)
            exists = result.scalar() is not None
            
            if not exists:
                logger.info(f"Adding column {column_name} to {table_name}")
                alter_query = text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
                conn.execute(alter_query)
                conn.commit()
                logger.info(f"Column {column_name} added successfully")
        except Exception as e:
            logger.error(f"Error adding column {column_name}: {e}")
    conn.close()

def create_and_test_database():
    """Create the database tables and test operations"""
    # Get database URL from environment
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    # Create engine and session
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create tables if they don't exist
        logger.info("Creating tables if they don't exist...")
        # Use reflect to check existing tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        if 'open_router_model' not in inspector.get_table_names():
            logger.info("Creating open_router_model table...")
            Base.metadata.create_all(engine, tables=[OpenRouterModel.__table__])
            logger.info("open_router_model table created")
        else:
            logger.info("open_router_model table already exists, adding missing columns...")
            # Define columns to add if missing
            columns_to_add = {
                'is_free': 'BOOLEAN DEFAULT FALSE',
                'supports_reasoning': 'BOOLEAN DEFAULT FALSE',
                'created_at': 'TIMESTAMP DEFAULT NOW()',
                'updated_at': 'TIMESTAMP DEFAULT NOW()'
            }
            add_columns_if_missing(engine, 'open_router_model', columns_to_add)
            
        logger.info("Tables setup completed")
        
        # Test database operations
        try:
            # Count existing models
            existing_count = session.query(OpenRouterModel).count()
            logger.info(f"Found {existing_count} existing models in the database")
            
            # Let's get a model from OpenRouter API
            logger.info("Fetching a model from OpenRouter API...")
            api_key = os.environ.get('OPENROUTER_API_KEY')
            if not api_key:
                logger.error("OPENROUTER_API_KEY environment variable not set")
                return False
                
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://openrouter.ai/api/v1/models',
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get models from API: {response.status_code} - {response.text}")
                return False
                
            # Get first model
            models_data = response.json()
            if not models_data.get('data'):
                logger.error("No models returned from API")
                return False
                
            # Take the first model for testing
            first_model = models_data['data'][0]
            model_id = first_model.get('id')
            
            if not model_id:
                logger.error("Model ID not found in response")
                return False
                
            logger.info(f"Got model {model_id} from API")
            
            # Check if this model exists in our database
            db_model = session.query(OpenRouterModel).filter_by(model_id=model_id).first()
            
            if db_model:
                logger.info(f"Model {model_id} already exists in database, updating it")
                db_model.name = first_model.get('name', '')
                db_model.updated_at = datetime.utcnow()
                db_model.last_fetched_at = datetime.utcnow()
            else:
                logger.info(f"Model {model_id} not found in database, creating it")
                # Create a new model entry
                new_model = OpenRouterModel(
                    model_id=model_id,
                    name=first_model.get('name', ''),
                    description=first_model.get('description', ''),
                    is_multimodal=False,  # For testing
                    is_free=False,        # For testing
                    supports_reasoning=True,  # For testing
                    cost_band='$$$',      # For testing
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    last_fetched_at=datetime.utcnow()
                )
                session.add(new_model)
                
            # Commit changes
            session.commit()
            logger.info("Database operations completed successfully")
            
            # Query all models to verify
            all_models = session.query(OpenRouterModel).all()
            logger.info(f"Found {len(all_models)} models in database after operations")
            
            # Log the first 3 models
            for i, model in enumerate(all_models[:3]):
                logger.info(f"Model {i+1}: {model.model_id}, Name: {model.name}")
                logger.info(f"  Created: {model.created_at}, Updated: {model.updated_at}")
                logger.info(f"  Capabilities: multimodal={model.is_multimodal}, free={model.is_free}, reasoning={model.supports_reasoning}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during database operations: {e}")
            session.rollback()
            return False
            
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    logger.info("Starting direct test of OpenRouterModel database...")
    success = create_and_test_database()
    
    if success:
        logger.info("Test completed successfully")
        sys.exit(0)
    else:
        logger.error("Test failed")
        sys.exit(1)