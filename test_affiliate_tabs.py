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
        'total_earned': '150.50',
        'pending': '25.00',
        'referrals': 12,
        'conversion_rate': '15.5'
    }
    
    # Mock commissions
    commissions = [
        {
            'id': 1,
            'created_at': datetime.now(),
            'amount': '10.50',
            'tier': 1,
            'status': 'approved'
        },
        {
            'id': 2,
            'created_at': datetime.now(),
            'amount': '5.25',
            'tier': 2,
            'status': 'pending'
        },
        {
            'id': 3,
            'created_at': datetime.now(),
            'amount': '15.00',
            'tier': 1,
            'status': 'paid'
        }
    ]
    
    # Mock referrals
    referrals = [
        {
            'id': 1,
            'username': 'user1',
            'created_at': datetime.now(),
            'total_purchases': '50.00'
        },
        {
            'id': 2,
            'username': 'user2',
            'created_at': datetime.now(),
            'total_purchases': '75.50'
        }
    ]
    
    # Mock sub-referrals
    sub_referrals = [
        {
            'id': 1,
            'username': 'sub_user1',
            'created_at': datetime.now(),
            'total_purchases': '25.00'
        }
    ]
    
    # For testing template rendering
    return render_template(
        'test_affiliate.html',
        user=user,
        affiliate=affiliate,
        commission_stats=commission_stats,
        commissions=commissions,
        referrals=referrals,
        sub_referrals=sub_referrals,
        stats=commission_stats  # Alias to match dashboard template
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)