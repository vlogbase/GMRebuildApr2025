"""
Test script to verify the Tell a Friend tab functionality
"""
import os
import sys
import logging
from flask import Flask, render_template, request, session, g

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create a simple test app
app = Flask(__name__)
app.secret_key = 'test_secret_key'

# Mock user class for testing
class User:
    """Mock User class for testing"""
    def __init__(self, id=1, username='test_user', email='test@example.com'):
        self.id = id
        self.username = username
        self.email = email
        self.paypal_email = 'paypal@example.com'
        self.referral_code = 'TEST123'
        self.is_authenticated = True
        
    def get_id(self):
        """Return user ID as string"""
        return str(self.id)
        
# Mock current_user
current_user = User()

@app.route('/')
def index():
    """Test route to render the account page with Tell a Friend tab"""
    # Mock data for template
    commission_stats = {
        'total_earned': '120.00',
        'pending': '45.00',
        'referrals': 5,
        'conversion_rate': 12
    }
    
    return render_template(
        'account.html', 
        current_user=current_user,
        commission_stats=commission_stats,
        referrals=[],
        sub_referrals=[],
        commissions=[]
    )

@app.route('/affiliate/tell-a-friend')
def tell_a_friend():
    """Mock route for Tell a Friend tab template"""
    return render_template(
        'affiliate/tell_friend_tab_simplified.html',
        current_user=current_user
    )

@app.context_processor
def utility_processor():
    """Add utility functions to template context"""
    def format_date(date):
        """Format a date for display"""
        if date:
            return date.strftime('%Y-%m-%d %H:%M:%S')
        return ''
        
    def format_currency(amount):
        """Format an amount as currency"""
        if amount:
            return f'${float(amount):.2f}'
        return '$0.00'
        
    def get_status_class(status):
        """Get CSS class for status display"""
        status_classes = {
            'pending': 'pending',
            'approved': 'approved',
            'paid': 'paid',
            'rejected': 'rejected'
        }
        return status_classes.get(status, '')
        
    return dict(
        format_date=format_date,
        format_currency=format_currency,
        get_status_class=get_status_class
    )

# Run the test application
if __name__ == '__main__':
    # Add template folder to allow rendering templates
    app.template_folder = 'templates'
    
    # Get port (default to 5000)
    port = int(os.environ.get("PORT", 5000))
    
    # Start the server
    logger.info(f"Starting test server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)