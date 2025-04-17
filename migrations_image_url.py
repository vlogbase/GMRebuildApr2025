"""
Database migration to add image_url column to Message table.
This is needed for multimodal chat functionality.
"""
from app import app, db
from sqlalchemy import Column, String, text

def migrate_database():
    """
    Apply database migration to add image_url column to Message table.
    
    This function should be run in the Flask application context.
    """
    try:
        print("Starting migration to add image_url column to Message table...")
        with app.app_context():
            # Check if column already exists to avoid errors
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('message')]
            
            if 'image_url' not in columns:
                # Add column - using the newer SQLAlchemy execute() method
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE message ADD COLUMN image_url VARCHAR(512)'))
                    conn.commit()
                print("Migration successful: Added image_url column to Message table")
            else:
                print("Column image_url already exists in Message table, skipping migration")
    except Exception as e:
        print(f"Migration error: {e}")
        raise

if __name__ == "__main__":
    # Run migration directly if executed as a script
    migrate_database()