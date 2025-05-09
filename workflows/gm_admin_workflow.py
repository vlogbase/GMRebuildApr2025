"""
GloriaMundo Admin Dashboard Workflow
A simple workflow for running the admin dashboard interface.
"""
import os
import sys
import logging
from pathlib import Path

# Add the parent directory to sys.path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('gm_admin.log')
    ]
)

logger = logging.getLogger(__name__)

def run():
    """Run the admin dashboard application."""
    # Set admin email
    os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com'
    logger.info(f"Admin emails set to: {os.environ.get('ADMIN_EMAILS')}")
    
    # Import Flask app 
    from app import app
    
    # Set debug mode
    app.debug = True
    
    # Start the application
    logger.info("Starting GloriaMundo Admin Dashboard on port 3000...")
    logger.info(f"Access dashboard at: http://localhost:3000/gm-admin")
    logger.info(f"Admin access restricted to: {os.environ.get('ADMIN_EMAILS')}")
    
    # Check if port 3000 is already in use
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 3000))
    if result == 0:
        logger.warning("Port 3000 is already in use. The admin dashboard may not start correctly.")
    sock.close()
    
    # Run the application on port 3000
    app.run(host='0.0.0.0', port=3000, debug=True)

if __name__ == "__main__":
    run()