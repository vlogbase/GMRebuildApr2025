"""
Test script to verify CSRF fixes are working properly.

This script runs the Flask application so we can test if the CSRF token fixes
have resolved the 400 Bad Request errors for AJAX endpoints.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    """
    Run the Flask application for testing CSRF fixes.
    """
    try:
        logger.info("Starting Flask application with CSRF fix test")
        
        # Import the Flask app
        from app import app
        
        # Set debug and testing modes
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        
        # Log CSRF protection status
        if app.config.get('WTF_CSRF_ENABLED', True):
            logger.info("CSRF protection is ENABLED")
        else:
            logger.warning("CSRF protection is DISABLED")
            
        # Log which routes are exempted from CSRF
        from flask_wtf.csrf import CSRFProtect
        csrf = next((ext for ext in app.extensions.values() 
                    if isinstance(ext, CSRFProtect)), None)
        
        if csrf:
            exempt_routes = getattr(csrf, '_exempt', [])
            logger.info(f"Routes exempt from CSRF: {exempt_routes}")
        
        # Instructions for testing
        logger.info("=" * 80)
        logger.info("CSRF FIX TEST INSTRUCTIONS")
        logger.info("=" * 80)
        logger.info("1. Access the site at http://localhost:5000")
        logger.info("2. Login to your account")
        logger.info("3. To run the CSRF tests, add ?test_csrf to the URL: http://localhost:5000/?test_csrf")
        logger.info("4. Click the 'Run CSRF Tests' button that appears in the top-right corner")
        logger.info("5. Check if all tests pass without 400 Bad Request errors")
        logger.info("=" * 80)
        
        # Start the Flask server
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"Error starting Flask application: {e}")
        raise

if __name__ == "__main__":
    main()