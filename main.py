from app import app

# Import models to ensure they're registered with the ORM
import models

# Initialize database tables
with app.app_context():
    from app import db
    db.create_all()
    
    # Run database migrations
    try:
        from migrations import migrate_database
        migrate_database()
    except Exception as e:
        print(f"Error running migrations: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)