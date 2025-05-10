"""
Standalone script to verify the admin dashboard functionality.
"""
import os
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Verify the admin dashboard is properly registered and accessible.
    """
    # Get environment variables
    admin_email = os.environ.get('ADMIN_EMAIL', 'andy@sentigral.com')
    port = os.environ.get('PORT', '3000')
    base_url = f"http://localhost:{port}"
    
    logger.info(f"Testing admin access for {admin_email} on {base_url}")
    
    # Check if server is running
    try:
        # Request the admin status endpoint
        r = requests.get(f"{base_url}/admin-status")
        
        if r.status_code == 200:
            logger.info("Admin status endpoint is accessible")
            data = r.json()
            logger.info(f"Admin routes: {data.get('admin_routes', [])}")
            logger.info(f"Admin emails: {data.get('admin_emails', '')}")
            logger.info(f"Admin accessible: {data.get('admin_accessible', False)}")
            
            # Check if we have the expected admin routes
            expected_routes = ['/admin', '/admin-direct', '/admin/check']
            missing_routes = [route for route in expected_routes if route not in data.get('admin_routes', [])]
            
            if missing_routes:
                logger.warning(f"Missing expected admin routes: {missing_routes}")
            else:
                logger.info("All expected admin routes are available")
                
        else:
            logger.error(f"Admin status endpoint returned status code {r.status_code}")
    
    except requests.RequestException as e:
        logger.error(f"Error connecting to admin dashboard: {str(e)}")
        logger.info("Make sure the server is running on the specified port")
    
if __name__ == "__main__":
    main()