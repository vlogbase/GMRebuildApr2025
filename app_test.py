"""
Test file to validate our JavaScript fixes
"""
from flask import Flask, render_template, g
from flask_login import LoginManager, current_user, AnonymousUserMixin

app = Flask(__name__)
app.secret_key = "testkey"

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Anonymous user for testing
class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.username = "Guest"
        self.email = "guest@example.com"
        self.id = None
        
    def is_authenticated(self):
        return False

# Register anonymous user loader
@login_manager.user_loader
def load_user(user_id):
    return None  # Always return None to simulate no logged-in user

# Set the anonymous user
login_manager.anonymous_user = Anonymous

@app.route('/')
def index():
    # Always pass is_logged_in=False to test the non-logged in state
    is_logged_in = False
    return render_template(
        'index.html',
        user=current_user,
        is_logged_in=is_logged_in,
        conversations=[]
    )

def main():
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()