"""
Deployment Setup for Replit

This script helps prepare the application for Replit deployment.
It adds necessary health check endpoints and ensures the application
can properly handle Replit's deployment health checks.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("deployment-setup")

def setup_deployment():
    """Configure the application for deployment on Replit"""
    
    logger.info("Starting deployment setup...")
    
    # Check if the app.py file exists
    if not os.path.exists('app.py'):
        logger.error("app.py file not found. Cannot continue with deployment setup.")
        return False
    
    # Check if main.py exists 
    if not os.path.exists('main.py'):
        logger.error("main.py file not found. Cannot continue with deployment setup.")
        return False
    
    # Read the content of app.py
    try:
        with open('app.py', 'r') as f:
            app_content = f.read()
    except Exception as e:
        logger.error(f"Error reading app.py: {e}")
        return False
    
    # Read the content of main.py
    try:
        with open('main.py', 'r') as f:
            main_content = f.read()
    except Exception as e:
        logger.error(f"Error reading main.py: {e}")
        return False
    
    # Check for health check routes
    if '@app.route(\'/health\')' not in app_content and '@app.route(\'/healthz\')' not in app_content:
        logger.info("Adding health check routes...")
        
        # Create the health check module
        with open('health_check.py', 'w') as f:
            f.write('''"""
Health check module for deployment

This module provides simple health check endpoints for deployment monitoring.
"""

import logging
from flask import Blueprint, Response, jsonify

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint for health check routes
health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring systems"""
    return jsonify({"status": "ok", "message": "Application is healthy"})
    
@health_bp.route('/healthz')
def kubernetes_health():
    """Kubernetes-style health check endpoint"""
    return Response("OK", status=200, mimetype='text/plain')

def init_app(app):
    """Register the health check blueprint with the Flask app"""
    app.register_blueprint(health_bp)
    logger.info("Health check routes registered")
''')
        logger.info("Created health_check.py with dedicated health check routes")

    # Update the main.py file to import health checks if not already present
    if "health_check import init_app" not in main_content:
        logger.info("Updating main.py to register health check routes...")
        
        # Find the appropriate position in main.py (after Flask app init, before run)
        if "if __name__ == \"__main__\":" in main_content:
            # Insert health check import before app.run
            main_lines = main_content.split('\n')
            main_idx = main_content.find("if __name__ == \"__main__\":")
            
            # Find a good insertion point before if __name__ == "__main__" 
            insert_line = main_idx
            
            # Working backwards to find a good insertion point after session initialization
            for i in range(main_lines.index("if __name__ == \"__main__\":") - 1, 0, -1):
                if "Flask session initialized" in main_lines[i]:
                    insert_line = i + 1
                    break
            
            # Add health check registration after Session initialization
            health_init = '''
# Register health check routes for deployment health checks
try:
    from health_check import init_app as init_health_check
    init_health_check(app)
    logger.info("Health check routes registered for deployment")
except ImportError as e:
    logger.warning(f"Could not import health check module: {e}")
except Exception as e:
    logger.error(f"Error registering health check routes: {e}")
'''
            
            # Insert after the specified line
            main_lines.insert(insert_line + 1, health_init)
            
            # Add explicit check for running with Gunicorn if not present
            if "app.run(" in main_content and not "else:" in main_content[main_idx:]:
                # Find the end of the if __name__ block
                if_block_end = -1
                in_if_block = False
                for i in range(len(main_lines)):
                    if main_lines[i].strip().startswith("if __name__ == \"__main__\":"):
                        in_if_block = True
                    elif in_if_block and main_lines[i].strip() and not main_lines[i].startswith(' ') and not main_lines[i].startswith('\t'):
                        if_block_end = i
                        break
                
                if if_block_end == -1:
                    if_block_end = len(main_lines)
                
                # Add Gunicorn detection in else block
                gunicorn_detection = '''else:
    # When running under Gunicorn, log the startup
    logger.info("Application loaded by Gunicorn")
    
    # Ensure robust exception handling during startup
    try:
        # Check if we can access critical resources
        import redis
        from redis_config import check_redis_health
        health_status = check_redis_health('session')
        if health_status.get('status') == 'available':
            logger.info("Redis connection verified: OK")
        else:
            logger.warning(f"Redis status: {health_status.get('status')}, Error: {health_status.get('error')}")
    except Exception as e:
        logger.error(f"Error during Gunicorn startup checks: {e}")
        # Continue anyway - don't fail deployment if Redis isn't available'''
                
                # Insert Gunicorn detection after the if __name__ block
                main_lines.insert(if_block_end, gunicorn_detection)
            
            # Write the updated content
            with open('main.py', 'w') as f:
                f.write('\n'.join(main_lines))
            
            logger.info("Updated main.py with health check registration")
    
    # Ensure the root route (/) responds to health checks
    if '@app.route(\'/\')' in app_content:
        logger.info("Root route (/) already exists in app.py")
        
        # Check if the root route handler responds appropriately to health checks
        if 'health' not in app_content[app_content.find('@app.route(\'/\')'):app_content.find('@app.route(\'/\')')+500]:
            logger.warning("Root route exists but may not handle health checks properly")
            logger.info("Consider updating the root route handler to respond to health checks")
    else:
        logger.warning("No root route (/) found in app.py")
        logger.info("Consider adding a root route that responds to health checks")
    
    logger.info("Deployment setup completed successfully!")
    return True

if __name__ == "__main__":
    if setup_deployment():
        print("\n✅ Deployment setup completed successfully!")
        print("\nYour application should now be ready for deployment on Replit.")
        print("The following changes have been made:")
        print("  1. Added dedicated health check routes (/health and /healthz)")
        print("  2. Ensured main.py is properly configured for Gunicorn")
        print("\nMake sure your .replit file has the correct deployment configuration:")
        print("  [deployment]")
        print("  run = [\"gunicorn\", \"main:app\", \"-k\", \"gevent\", \"-w\", \"4\", \"--timeout\", \"300\", \"--bind\", \"0.0.0.0:5000\"]")
        print("\n  [[ports]]")
        print("  localPort = 5000")
        print("  externalPort = 80")
    else:
        print("\n❌ Deployment setup failed. See the logs above for details.")
    
    sys.exit(0 if setup_deployment() else 1)