from app import app

# Import models to ensure they're registered with the ORM
import models

# Initialize database tables
with app.app_context():
    from app import db
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)