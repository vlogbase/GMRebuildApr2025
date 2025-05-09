"""
Debug script to test admin tab visibility on the account page.
This script directly renders the account page with the admin tab selected.
"""

import os
import logging
from flask import Flask, render_template, url_for, request, g
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a minimal Flask app for testing
app = Flask(__name__)
app.secret_key = 'debug_secret_key'

# Mock current user and authentication for testing
class MockUser:
    def __init__(self, email, is_admin=False):
        self.email = email
        self._is_admin = is_admin
        self.id = 1
    
    def get_balance_usd(self):
        return 100.0
    
    def is_authenticated(self):
        return True

# Mock affiliate
class MockAffiliate:
    def __init__(self, id, name, email, status="active"):
        self.id = id
        self.name = name
        self.email = email
        self.status = status

# Mock commission
class MockCommission:
    def __init__(self, id, affiliate, status, amount, purchase_amount, level=1):
        self.id = id
        self.affiliate = affiliate
        self.status = status
        self.commission_amount = amount
        self.purchase_amount_base = purchase_amount
        self.commission_level = level
        self.commission_earned_date = datetime.now() - timedelta(days=30)
        self.commission_available_date = datetime.now() - timedelta(days=5)
        self.triggering_transaction_id = f"{1}_transaction"

# Register context processors for templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.context_processor
def inject_csrf_token():
    return {'csrf_token': lambda: 'mock_csrf_token'}

# Mock admin status check
def is_admin():
    return True if hasattr(g, 'user') and g.user._is_admin else False

# Test route for account page with admin tab
@app.route('/debug-admin')
def debug_admin_tab():
    # Set up mock data for testing
    g.user = MockUser('andy@sentigral.com', is_admin=True)
    
    # Create mock affiliate data
    mock_affiliate = MockAffiliate(1, "Andy Admin", "andy@sentigral.com")
    
    # Create mock commissions
    mock_commissions = [
        MockCommission(1, mock_affiliate, "held", 10.0, 100.0),
        MockCommission(2, mock_affiliate, "approved", 15.0, 150.0),
        MockCommission(3, mock_affiliate, "paid", 5.0, 50.0),
        MockCommission(4, mock_affiliate, "rejected", 2.0, 20.0)
    ]
    
    # Create mock packages and transactions
    mock_packages = [
        {"id": 1, "amount_usd": 5.0, "stripe_price_id": "price_1RKOl0CkgfcNKUGFhI5RljJd"},
        {"id": 2, "amount_usd": 10.0, "stripe_price_id": "price_2"},
        {"id": 3, "amount_usd": 25.0, "stripe_price_id": "price_3"},
        {"id": 4, "amount_usd": 100.0, "stripe_price_id": "price_4"}
    ]
    
    mock_transactions = []
    mock_usage = []
    
    # Simulate query parameters for tab selection
    request.args = {"tab": "admin"}
    
    # Render the template with mock data
    return render_template(
        'account.html',
        user=g.user,
        is_admin=is_admin(),
        admin_commissions=mock_commissions,
        packages=mock_packages,
        recent_transactions=mock_transactions,
        recent_usage=mock_usage
    )

# Run the app if this script is executed directly
if __name__ == '__main__':
    # Print debug information
    print("Starting debug server for admin tab testing...")
    print(f"Test URL: http://localhost:5000/debug-admin")
    print("This will render the account page with the admin tab selected.")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)