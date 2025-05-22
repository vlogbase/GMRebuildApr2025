"""
Workflow configuration file for testing PayPal email update functionality
"""

def run():
    """
    Run the Flask application for testing
    """
    from app import app
    
    # Configure app for testing
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable browser caching
    
    # Run the server
    app.run(host='0.0.0.0', port=5000, debug=True)