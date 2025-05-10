"""
Simple script to test admin access and functionality.
"""
import os
import sys
import logging
from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_admin.log')
    ]
)
logger = logging.getLogger(__name__)

# Create a minimal Flask application for testing
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = 'admin_test_secret_key'  # For testing only
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Set up login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define simplified models for testing
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Affiliate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    paypal_email = db.Column(db.String(120))
    referral_code = db.Column(db.String(20), unique=True)
    status = db.Column(db.String(20), default='active')
    terms_agreed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Affiliate {self.name}>'

class Commission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliate.id'))
    referred_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    commission_level = db.Column(db.Integer, default=1) # 1=direct, 2=second tier
    purchase_amount_base = db.Column(db.Float)
    commission_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')
    commission_earned_date = db.Column(db.DateTime)
    commission_available_date = db.Column(db.DateTime)
    payout_batch_id = db.Column(db.String(64))
    
    # Define relationships
    affiliate = db.relationship('Affiliate', backref=db.backref('commissions', lazy=True))
    user = db.relationship('User', backref=db.backref('referred_commissions', lazy=True))
    
    def __repr__(self):
        return f'<Commission {self.id} - £{self.commission_amount}>'

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {e}")
        return None

# Basic routes for testing
@app.route('/')
def index():
    return '''
    <h1>Admin Test Application</h1>
    <p>Testing Flask-Admin integration.</p>
    <p><a href="/admin">Admin Dashboard</a></p>
    <p><a href="/admin-check">Admin Check</a></p>
    '''

@app.route('/login')
def login():
    return '''
    <h1>Login</h1>
    <p>This is a placeholder login page. In a real application, you would handle authentication here.</p>
    <p>For testing, use andy@sentigral.com as the admin email.</p>
    '''

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

# Create admin user for testing
def create_test_data():
    try:
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Check if admin user exists
            admin_user = User.query.filter_by(email='andy@sentigral.com').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='andy@sentigral.com',
                    password_hash=generate_password_hash('admin'),
                    created_at=db.func.now()
                )
                db.session.add(admin_user)
                logger.info("Created admin user")
            
            # Add some test data
            if db.session.query(Affiliate).count() == 0:
                # Create a test affiliate
                test_affiliate = Affiliate(
                    user_id=1,
                    name='Test Affiliate',
                    email='affiliate@example.com',
                    paypal_email='affiliate@paypal.com',
                    referral_code='TESTREF',
                    status='active',
                    terms_agreed_at=db.func.now(),
                    created_at=db.func.now()
                )
                db.session.add(test_affiliate)
                
                # Create a test commission
                test_commission = Commission(
                    affiliate_id=1,
                    referred_user_id=1,
                    commission_level=1,
                    purchase_amount_base=100.00,
                    commission_amount=20.00,
                    status='pending',
                    commission_earned_date=db.func.now(),
                    commission_available_date=db.func.now()
                )
                db.session.add(test_commission)
                
                logger.info("Created test affiliate and commission data")
            
            db.session.commit()
            logger.info("Test data committed to database")
    except Exception as e:
        logger.error(f"Error creating test data: {e}")
        import traceback
        logger.error(traceback.format_exc())

def run():
    """
    Run the admin test.
    """
    try:
        # Set admin emails environment variable
        if 'ADMIN_EMAILS' not in os.environ:
            os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
            logger.info(f"Set ADMIN_EMAILS environment variable to: {os.environ['ADMIN_EMAILS']}")
        
        # Create test data
        create_test_data()
        
        # Import and initialize the admin interface
        from simple_admin import create_admin
        
        # Create and initialize the admin interface
        logger.info("Initializing Flask-Admin interface")
        admin = create_admin(app, db)
        
        # Log successful initialization
        if admin:
            logger.info("Flask-Admin interface successfully initialized")
            
            # List all registered routes for diagnostics
            admin_routes = [rule.rule for rule in app.url_map.iter_rules() if 'admin' in rule.rule]
            logger.info(f"Registered admin routes: {admin_routes}")
        else:
            logger.error("Flask-Admin initialization returned None")
        
        # Get the port from environment or use 3000 for testing
        port = int(os.environ.get('PORT', 3000))
        
        # Run the app
        logger.info(f"Starting Flask test application with admin interface on port {port}")
        app.run(host="0.0.0.0", port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Error running admin test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    run()