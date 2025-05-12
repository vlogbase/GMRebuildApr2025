"""
Simple server to test the multi-level sorting functionality
"""

import os
import http.server
import socketserver

def run():
    """
    Run the simple HTTP server for testing the sorting functionality
    """
    # Change to the root directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    PORT = 5000
    Handler = http.server.SimpleHTTPRequestHandler
    
    # Custom handler to redirect '/' to the test page
    class TestHandler(Handler):
        def do_GET(self):
            if self.path == '/':
                self.path = '/test_sorting.html'
            return Handler.do_GET(self)
    
    with socketserver.TCPServer(("0.0.0.0", PORT), TestHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        print(f"To test the multi-level sorting, visit: http://localhost:{PORT}")
        print("In Replit, you can access the page directly")
        httpd.serve_forever()

if __name__ == "__main__":
    run()