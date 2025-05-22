"""
Fix deployment issues with the simplified affiliate system
"""
import os
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_app_imports():
    """Fix any import issues in app.py that might be causing deployment failures"""
    try:
        # Read app.py
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Create backup
        backup_path = f"app.py.bak.{int(time.time())}"
        with open(backup_path, 'w') as f:
            f.write(content)
        logger.info(f"Created backup at {backup_path}")
        
        # Check if we need to fix the simplified_affiliate_bp import
        if "simplified_affiliate_bp" in content and "ImportError as e:" not in content:
            # Add error handling for the import
            import_block = content.find("from simplified_affiliate import simplified_affiliate_bp")
            if import_block > 0:
                line_end = content.find('\n', import_block)
                updated_content = (
                    content[:import_block] + 
                    "try:\n    from simplified_affiliate import simplified_affiliate_bp\n" +
                    "    logger.info('Successfully imported simplified_affiliate_bp')\n" +
                    "except ImportError as e:\n" +
                    "    logger.warning(f'Could not import simplified_affiliate_bp: {e}')\n" +
                    "    simplified_affiliate_bp = None" +
                    content[line_end:]
                )
                
                # Write updated content
                with open('app.py', 'w') as f:
                    f.write(updated_content)
                logger.info("Added error handling for simplified_affiliate_bp import")
                return True
        else:
            logger.info("Import error handling already exists or simplified_affiliate_bp not found")
        
        return False
    except Exception as e:
        logger.error(f"Error fixing app imports: {e}")
        return False

def fix_blueprint_registration():
    """Fix how simplified_affiliate_bp is registered to handle None case"""
    try:
        # Read app.py
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Check if we need to fix blueprint registration
        register_line = content.find("app.register_blueprint(simplified_affiliate_bp)")
        if register_line > 0 and "if simplified_affiliate_bp is not None" not in content:
            # Add conditional registration
            line_start = content.rfind('\n', 0, register_line)
            line_end = content.find('\n', register_line)
            
            updated_content = (
                content[:line_start] + 
                "\n# Register simplified affiliate blueprint if available\n" +
                "if simplified_affiliate_bp is not None:\n" +
                "    app.register_blueprint(simplified_affiliate_bp)\n" +
                "    logger.info('Registered simplified_affiliate_bp')\n" +
                content[line_end+1:]
            )
            
            # Write updated content
            with open('app.py', 'w') as f:
                f.write(updated_content)
            logger.info("Added conditional registration for simplified_affiliate_bp")
            return True
        else:
            logger.info("Blueprint registration already has error handling or not found")
        
        return False
    except Exception as e:
        logger.error(f"Error fixing blueprint registration: {e}")
        return False

def ensure_port_binding():
    """Make sure main.py binds to the right port for deployment"""
    try:
        # Read main.py
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Create backup
        backup_path = f"main.py.bak.{int(time.time())}"
        with open(backup_path, 'w') as f:
            f.write(content)
        logger.info(f"Created backup at {backup_path}")
        
        # Look for the port binding line
        port_line = content.find("app.run(host='0.0.0.0', port=5000")
        if port_line > 0:
            # Update to use PORT environment variable with fallback
            line_start = content.rfind('\n', 0, port_line)
            line_end = content.find('\n', port_line)
            
            updated_content = (
                content[:line_start] + 
                "\n    # Use PORT environment variable for Cloud Run compatibility\n" +
                "    port = int(os.environ.get('PORT', 5000))\n" +
                f"    app.run(host='0.0.0.0', port=port, debug=True)\n" +
                content[line_end+1:]
            )
            
            # Write updated content
            with open('main.py', 'w') as f:
                f.write(updated_content)
            logger.info("Updated port binding to use PORT environment variable")
            return True
        else:
            logger.info("Could not find port binding line or already updated")
        
        return False
    except Exception as e:
        logger.error(f"Error ensuring port binding: {e}")
        return False

def ensure_gunicorn_config():
    """Update .replit deployment configuration for gunicorn"""
    try:
        # Read .replit file
        with open('.replit', 'r') as f:
            content = f.read()
        
        # Create backup
        backup_path = f".replit.bak.{int(time.time())}"
        with open(backup_path, 'w') as f:
            f.write(content)
        logger.info(f"Created backup at {backup_path}")
        
        # Look for the deployment run line
        run_line = content.find('run = ["gunicorn", "main:app"')
        if run_line > 0:
            # Update to ensure correct configuration
            line_start = content.rfind('\n', 0, run_line)
            line_end = content.find('\n', run_line)
            
            # Get the existing line to preserve options
            existing_line = content[run_line:line_end]
            
            # Check if it already has the key settings
            has_bind = 'bind' in existing_line
            has_workers = 'workers' in existing_line
            has_timeout = 'timeout' in existing_line
            
            # Build the updated line
            updated_line = 'run = ["gunicorn", "main:app"'
            if not has_workers:
                updated_line += ', "-w", "4"'
            if not has_timeout:
                updated_line += ', "--timeout", "300"'
            if not has_bind:
                updated_line += ', "--bind", "0.0.0.0:${PORT:-5000}"'
            
            # Add the end of the original line (preserving other options)
            updated_line += existing_line[existing_line.find(']'):]
            
            updated_content = (
                content[:run_line] + 
                updated_line +
                content[line_end:]
            )
            
            # Write updated content
            with open('.replit', 'w') as f:
                f.write(updated_content)
            logger.info("Updated gunicorn configuration in .replit")
            return True
        else:
            logger.info("Could not find gunicorn run line or already updated")
        
        return False
    except Exception as e:
        logger.error(f"Error updating gunicorn config: {e}")
        return False

def fix_deployment_issues():
    """Fix all deployment issues"""
    logger.info("Starting deployment fixes")
    
    # Apply fixes
    import_fixed = fix_app_imports()
    blueprint_fixed = fix_blueprint_registration()
    port_fixed = ensure_port_binding()
    gunicorn_fixed = ensure_gunicorn_config()
    
    # Summary
    logger.info("\n=== Fix Summary ===")
    logger.info(f"App imports: {'Fixed' if import_fixed else 'No changes needed'}")
    logger.info(f"Blueprint registration: {'Fixed' if blueprint_fixed else 'No changes needed'}")
    logger.info(f"Port binding: {'Fixed' if port_fixed else 'No changes needed'}")
    logger.info(f"Gunicorn config: {'Fixed' if gunicorn_fixed else 'No changes needed'}")
    
    if import_fixed or blueprint_fixed or port_fixed or gunicorn_fixed:
        logger.info("\nChanges made! Deployment should now work correctly.")
    else:
        logger.info("\nNo changes were needed. If deployment still fails, check for other issues.")
    
    return import_fixed or blueprint_fixed or port_fixed or gunicorn_fixed

if __name__ == "__main__":
    fix_deployment_issues()