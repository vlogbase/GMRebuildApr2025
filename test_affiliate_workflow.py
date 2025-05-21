"""
Test workflow for the affiliate system functionality.
This workflow specifically tests the affiliate dashboard and PayPal email update.
"""

def run():
    """Run the Flask application for testing the affiliate system"""
    import logging
    from app import app
    
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Register routes correctly
    logger.info("Starting affiliate test workflow")
    logger.info("Registered routes:")
    for rule in app.url_map.iter_rules():
        if "affiliate" in rule.endpoint:
            logger.info(f"  {rule.endpoint} - {rule}")
    
    # Run the app with debug enabled
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()