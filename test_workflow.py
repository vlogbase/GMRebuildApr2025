"""
Simplified workflow script to test the Tell a Friend tab in account.html
"""
import logging
import sys
from flask import Flask, render_template, session

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a simple Flask app
app = Flask(__name__)
app.secret_key = "test_secret_key"

@app.route('/')
def index():
    """Render the test account page with Tell a Friend tab selected"""
    # Set a user in session so templates work
    session['user_id'] = 1
    return render_template('test_affiliate.html')

def run():
    """Run the Flask application"""
    logger.info("Starting test server for Tell a Friend tab")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()