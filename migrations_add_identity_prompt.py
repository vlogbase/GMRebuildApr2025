"""
Database migration to add the enable_identity_prompt column to the User table.
"""
import logging
from app import app, db
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Adds the enable_identity_prompt column to the user table."""
    with app.app_context():
        try:
            # Check if the column already exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('user')]
            if 'enable_identity_prompt' in columns:
                logger.info("Column 'enable_identity_prompt' already exists in 'user' table. Skipping migration.")
                return

            # Add the column with a default value of TRUE
            logger.info("Adding 'enable_identity_prompt' column to 'user' table...")
            with db.engine.connect() as connection:
                connection.execute(text("ALTER TABLE \"user\" ADD COLUMN enable_identity_prompt BOOLEAN NOT NULL DEFAULT TRUE;"))
                connection.commit()
            logger.info("Migration successful.")

        except Exception as e:
            logger.error(f"An error occurred during migration: {e}")

if __name__ == "__main__":
    run_migration()