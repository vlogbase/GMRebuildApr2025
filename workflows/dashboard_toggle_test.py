"""
Simple HTTP server to test the affiliate dashboard toggle functionality.
"""

import http.server
import socketserver
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run():
    """
    Run a simple HTTP server to test the affiliate dashboard toggle.
    """
    try:
        logger.info("Starting HTTP server for affiliate dashboard toggle test")
        
        # Set the directory where the HTML file is located
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Define the handler and server
        Handler = http.server.SimpleHTTPRequestHandler
        
        # Use port 3000
        port = 3000
        with socketserver.TCPServer(("0.0.0.0", port), Handler) as httpd:
            logger.info(f"Server started at http://0.0.0.0:{port}")
            logger.info("Visit the test page at http://0.0.0.0:3000/test_affiliate_dashboard_toggle.html")
            httpd.serve_forever()
            
    except Exception as e:
        logger.error(f"Error running test server: {str(e)}")
        
if __name__ == "__main__":
    run()