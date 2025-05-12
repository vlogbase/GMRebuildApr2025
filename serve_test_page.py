"""
Simple HTTP server to serve the sorting test page
"""

import http.server
import socketserver
import os

# Set to True to enable verbose logging
DEBUG = True

# Define the handler
class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve test_sorting.html"""
    
    def log_message(self, format, *args):
        """Override to control logging verbosity"""
        if DEBUG:
            super().log_message(format, *args)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.path = '/test_sorting.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

# Set up and start the server
def main():
    """Start the HTTP server"""
    PORT = 5000
    
    Handler = SimpleHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"Server running at http://localhost:{PORT}")
            print(f"To test the multi-level sorting, visit: http://localhost:{PORT}")
            print("In Replit, you can access the page at:")
            print(f"https://$REPL_SLUG.$REPL_OWNER.repl.co")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()