"""
Test workflow for the Tell a Friend tab in the account page

This workflow runs a test server that will allow us to check if the 
Tell a Friend tab is displaying correctly without the "Almost Ready!" message.
"""

import os
import sys
import logging
from flask import Flask, render_template, session

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_app():
    """Create a simple Flask app for testing the Tell a Friend tab"""
    app = Flask(__name__)
    app.secret_key = "test_secret_key"

    @app.route('/')
    def index():
        """Render the account page with Tell a Friend tab selected"""
        # Set a user in session so templates work
        session['user_id'] = 1
        return render_template('test_affiliate.html')
    
    @app.route('/affiliate/tell-a-friend')
    def tell_a_friend():
        """Render the simplified Tell a Friend tab content directly"""
        session['user_id'] = 1
        return render_template('affiliate/tell_friend_tab_simplified.html', 
                              current_user={'referral_code': 'TEST1234'})
    
    return app

def run():
    """Run the test Flask application"""
    app = create_test_app()
    logger.info("Starting test server for Tell a Friend tab")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()