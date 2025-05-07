"""
Test file to verify the affiliate tab templates are working correctly
"""

import os
from flask import Flask, render_template, url_for
from datetime import datetime
from enum import Enum

# Create a simple app for testing
app = Flask(__name__)
app.secret_key = "test_secret_key"

# Mock classes for testing
class AffiliateStatus(Enum):
    PENDING_TERMS = "pending_terms"
    ACTIVE = "active"
    SUSPENDED = "suspended"

class CommissionStatus(Enum):
    HELD = "held"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"

class User:
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

class Affiliate:
    def __init__(self, id, email, referral_code, status, paypal_email=None):
        self.id = id
        self.email = email
        self.referral_code = referral_code
        self.status = status
        self.paypal_email = paypal_email

@app.route('/')
def test_page():
    # Create mock data
    user = User(1, "testuser", "test@example.com")
    
    # Test with an active affiliate
    affiliate = Affiliate(
        id=1,
        email="test@example.com",
        referral_code="ABC123",
        status=AffiliateStatus.ACTIVE.value,
        paypal_email="paypal@example.com"
    )
    
    # Test with commission stats
    commission_stats = {
        'total_earned': '$150.50',
        'pending': '$25.00',
        'referrals': 12
    }
    
    # For testing template rendering
    return render_template(
        'test_affiliate.html',
        user=user,
        affiliate=affiliate,
        commission_stats=commission_stats
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)