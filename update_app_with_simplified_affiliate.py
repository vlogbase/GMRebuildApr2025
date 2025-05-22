"""
Update app.py to use the simplified affiliate blueprint
"""
import os
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_imports():
    """Update imports in app.py to include the simplified affiliate blueprint"""
    try:
        # Read the file
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Create backup
        backup_path = f"app.py.bak.{int(time.time())}"
        with open(backup_path, 'w') as f:
            f.write(content)
        logger.info(f"Created backup of app.py at {backup_path}")
        
        # Add import for simplified affiliate blueprint if not already imported
        if "from simplified_affiliate import simplified_affiliate_bp" not in content:
            # Find where blueprints are imported
            import_block = content.find("from billing import billing_bp")
            if import_block == -1:
                import_block = content.find("# Import blueprints")
            
            if import_block != -1:
                # Find the end of the import block (next blank line)
                end_of_imports = content.find('\n\n', import_block)
                if end_of_imports != -1:
                    # Insert our import
                    updated_content = (
                        content[:end_of_imports] +
                        "\nfrom simplified_affiliate import simplified_affiliate_bp" +
                        content[end_of_imports:]
                    )
                    
                    # Write updated content
                    with open('app.py', 'w') as f:
                        f.write(updated_content)
                    
                    logger.info("Added import for simplified_affiliate_bp")
                    return True
        
        logger.info("Import for simplified_affiliate_bp already exists or couldn't find import block")
        return False
    except Exception as e:
        logger.error(f"Error updating imports: {e}")
        return False

def register_blueprint():
    """Register the simplified affiliate blueprint in app.py"""
    try:
        # Read the file
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Check if the blueprint is already registered
        if "app.register_blueprint(simplified_affiliate_bp)" not in content:
            # Find where blueprints are registered
            register_block = content.find("app.register_blueprint(billing_bp)")
            if register_block == -1:
                register_block = content.find("# Register blueprints")
            
            if register_block != -1:
                # Find the end of the register block
                line_end = content.find('\n', register_block)
                if line_end != -1:
                    # Insert our register statement
                    updated_content = (
                        content[:line_end+1] +
                        "app.register_blueprint(simplified_affiliate_bp)\n" +
                        content[line_end+1:]
                    )
                    
                    # Write updated content
                    with open('app.py', 'w') as f:
                        f.write(updated_content)
                    
                    logger.info("Registered simplified_affiliate_bp")
                    return True
        
        logger.info("simplified_affiliate_bp already registered or couldn't find register block")
        return False
    except Exception as e:
        logger.error(f"Error registering blueprint: {e}")
        return False

def main():
    """Run all updates"""
    logger.info("Starting app.py update")
    
    # Update imports
    if not update_imports():
        logger.error("Failed to update imports")
        return False
    
    # Register blueprint
    if not register_blueprint():
        logger.error("Failed to register blueprint")
        return False
    
    logger.info("Successfully updated app.py")
    return True

if __name__ == "__main__":
    main()