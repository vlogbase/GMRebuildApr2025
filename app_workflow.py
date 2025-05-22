"""
Simple Flask server workflow for GloriaMundo app
"""

import os
from app import app

def run():
    """Run the Flask application"""
    # Set debug mode
    app.debug = True
    
    # Use 0.0.0.0 to make the server accessible externally
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    run()