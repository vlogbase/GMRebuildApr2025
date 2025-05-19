"""
Simple Flask server workflow for GloriaMundo

This workflow runs the main Flask application with Redis caching and session support.
"""

import os
import sys
import logging

def run():
    """
    Run the Flask application
    """
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting GloriaMundo application workflow")
    
    # Import and run the app
    try:
        import main
        logger.info("Application imported successfully")
        
        # Print Redis environment variables (without passwords)
        redis_host = os.environ.get('REDIS_HOST', 'Not configured')
        redis_port = os.environ.get('REDIS_PORT', 'Not configured')
        ssl_enabled = os.environ.get('REDIS_SSL', 'Not configured')
        
        logger.info(f"Redis configuration: host={redis_host}, port={redis_port}, ssl={ssl_enabled}")
        
        # Run the app on port 5000, accessible externally
        from main import app
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)

if __name__ == "__main__":
    run()