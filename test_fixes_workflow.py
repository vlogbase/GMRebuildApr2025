"""
Test workflow to verify the credit validation and conversation loading fixes
"""
import os
import sys

def run():
    """Run the Flask application to test fixes"""
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Import and run the app
    from app import app
    print("Starting Flask app to test fixes...")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()