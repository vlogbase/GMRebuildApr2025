"""
Simple HTTP server to serve our test HTML page for PDF attachment testing
"""
import http.server
import socketserver
import webbrowser
import os
import logging
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define port and HTML file
PORT = 8000
TEST_FILE = 'test_pdf_attachment.html'

class TestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for serving our test page"""
    def do_GET(self):
        """Handle GET requests"""
        # Log the request
        logger.info(f"GET request for {self.path}")
        
        # Redirect root to our test page
        if self.path == '/' or self.path == '':
            self.path = f'/{TEST_FILE}'
            
        # Handle the request normally
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def log_message(self, format, *args):
        """Customize logging to use our logger"""
        logger.info("%s - %s" % (self.client_address[0], format % args))

def serve_test_page():
    """Start the server and open the browser"""
    # Check if our test file exists
    if not os.path.exists(TEST_FILE):
        logger.error(f"Test file {TEST_FILE} not found!")
        return False
    
    # Start the server
    with socketserver.TCPServer(("", PORT), TestHandler) as httpd:
        url = f"http://localhost:{PORT}/{TEST_FILE}"
        logger.info(f"Serving at port {PORT}")
        logger.info(f"Open your browser to {url}")
        
        # Try to open the browser automatically
        try:
            webbrowser.open(url)
        except Exception as e:
            logger.warning(f"Could not open browser automatically: {str(e)}")
            logger.info(f"Please open {url} manually in your browser")
            
        try:
            # Keep server running until interrupted
            logger.info("Press Ctrl+C to stop the server")
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
            return True
        
if __name__ == "__main__":
    serve_test_page()