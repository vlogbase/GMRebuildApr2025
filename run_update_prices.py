"""
Script to run update_stripe_test_prices.py within the Flask application context.
"""

from app import app
from update_stripe_test_prices import run

# Run the updates within the Flask application context
with app.app_context():
    print("Running update_stripe_test_prices.py within app context...")
    success = run()
    if success:
        print("Successfully updated database with test price IDs")
    else:
        print("Failed to update database with test price IDs")