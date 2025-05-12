"""
Database migration to add pdf_url and pdf_filename columns to Message table.
This is needed for PDF document handling functionality.
"""
from app import app, db
from sqlalchemy import Column, String, text

def migrate_database():
    """
    Apply database migration to add pdf_url and pdf_filename columns to Message table.
    
    This function should be run in the Flask application context.
    """
    try:
        print("Starting migration to add PDF support columns to Message table...")
        with app.app_context():
            # Check if columns already exist to avoid errors
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('message')]
            
            changes_made = False
            
            if 'pdf_url' not in columns:
                # Add pdf_url column
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE message ADD COLUMN pdf_url VARCHAR(512)'))
                    conn.commit()
                print("Migration step 1 successful: Added pdf_url column to Message table")
                changes_made = True
            else:
                print("Column pdf_url already exists in Message table, skipping")
                
            if 'pdf_filename' not in columns:
                # Add pdf_filename column
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE message ADD COLUMN pdf_filename VARCHAR(256)'))
                    conn.commit()
                print("Migration step 2 successful: Added pdf_filename column to Message table")
                changes_made = True
            else:
                print("Column pdf_filename already exists in Message table, skipping")
                
            if changes_made:
                print("PDF support migration completed successfully!")
            else:
                print("No changes needed - PDF support columns already exist")
    except Exception as e:
        print(f"Migration error: {e}")
        raise

if __name__ == "__main__":
    # Run migration directly if executed as a script
    migrate_database()