"""
Simple test script to verify the fix for non-authenticated users sidebar loading issue
"""
from flask import Flask, render_template
from flask_login import LoginManager, AnonymousUserMixin, current_user

app = Flask(__name__)
app.secret_key = "test_secret_key"

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Create anonymous user class
class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.username = "Guest"
        self.email = "guest@example.com"
        self.id = None
    
    def is_authenticated(self):
        return False

# Set anonymous user
login_manager.anonymous_user = Anonymous

@login_manager.user_loader
def load_user(user_id):
    # Always return None for testing
    return None

@app.route('/')
def index():
    """Main route to test template rendering with non-authenticated user"""
    # For testing, always set is_logged_in to False
    is_logged_in = current_user.is_authenticated
    
    print(f"User is logged in: {is_logged_in}")
    print(f"User authentication status: {current_user.is_authenticated}")
    
    return render_template(
        'index.html',
        user=current_user,
        is_logged_in=is_logged_in,
        conversations=[]
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)