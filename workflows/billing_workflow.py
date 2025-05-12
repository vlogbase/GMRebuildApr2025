"""
Script to run the Flask application for testing billing functionality.
This includes the pricing table with PDF capabilities and multi-level sorting.
"""

import os
import logging
from flask import Flask
from flask.logging import default_handler

def run():
    """
    Run the Flask application with error handling and logging.
    """
    try:
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename='app_output.log',
            filemode='a'
        )
        
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
        
        # Run the Flask app
        logging.info("Starting billing workflow with Flask app")
        os.environ["FLASK_DEBUG"] = "True"
        
        # Import the Flask app (importing here to avoid circular imports)
        from app import app
        
        # Register blueprints if they haven't been registered in app.py
        try:
            from billing import billing_bp
            app.register_blueprint(billing_bp)
            logging.info("Registered billing blueprint")
        except Exception as e:
            logging.error(f"Error registering billing blueprint: {e}")
        
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logging.error(f"Error in billing workflow: {e}", exc_info=True)

if __name__ == "__main__":
    run()