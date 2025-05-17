"""
Deployment Fix Script

This script analyzes and fixes common deployment issues in the GloriaMundo application.
It specifically targets:
1. SQLAlchemy initialization issues
2. Azure Blob Storage configuration
3. Gunicorn configuration for deployment
"""

import os
import shutil
import logging
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def backup_file(filepath):
    """Create a backup of a file before modifying it"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.bak.{timestamp}"
    try:
        shutil.copy2(filepath, backup_path)
        logger.info(f"Created backup at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup of {filepath}: {e}")
        return False

def read_file(filepath):
    """Read the contents of a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Failed to read {filepath}: {e}")
        return None

def write_file(filepath, content):
    """Write content to a file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"Successfully updated {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to write to {filepath}: {e}")
        return False

def fix_sqlalchemy_initialization(app_py_path, main_py_path):
    """Fix SQLAlchemy initialization to avoid duplicate registration"""
    logger.info("Fixing SQLAlchemy initialization...")
    
    # Check and fix main.py
    main_content = read_file(main_py_path)
    if main_content:
        if "init_db(app)" in main_content:
            # Replace init_db with db.init_app
            new_main_content = main_content.replace(
                "from database import db, init_db\ninit_db(app)",
                "from database import db\ndb.init_app(app)"
            )
            if new_main_content != main_content:
                if backup_file(main_py_path):
                    write_file(main_py_path, new_main_content)
                    logger.info("Updated SQLAlchemy initialization in main.py")
    
    # Check and fix app.py
    app_content = read_file(app_py_path)
    if app_content:
        if "init_db(app)" in app_content:
            # Replace init_db with db.init_app
            new_app_content = app_content.replace(
                "from database import init_db\ninit_db(app)",
                "from database import db\ndb.init_app(app)"
            )
            if new_app_content != app_content:
                if backup_file(app_py_path):
                    write_file(app_py_path, new_app_content)
                    logger.info("Updated SQLAlchemy initialization in app.py")

def fix_azure_blob_storage(app_py_path):
    """Fix Azure Blob Storage imports and initialization"""
    logger.info("Fixing Azure Blob Storage configuration...")
    
    app_content = read_file(app_py_path)
    if not app_content:
        return
    
    # Check if BlobServiceClient is imported properly
    if "BlobServiceClient" in app_content and "from azure.storage.blob import BlobServiceClient" not in app_content:
        # Add proper imports
        azure_import = "from azure.storage.blob import BlobServiceClient, ContentSettings"
        
        # Find a good location to insert the import
        import_match = re.search(r'# Initialize Azure Blob Storage.*?try:', app_content, re.DOTALL)
        if import_match:
            start, end = import_match.span()
            new_content = app_content[:end] + f"\n    {azure_import}\n" + app_content[end:]
            
            if backup_file(app_py_path):
                write_file(app_py_path, new_content)
                logger.info("Added Azure Blob Storage imports to app.py")

def fix_gunicorn_config():
    """Fix gunicorn configuration for deployment"""
    logger.info("Setting up correct gunicorn configuration...")
    
    # Create or update .replit.workflow file
    workflow_content = """[Start application]
priority = 50
autoWatch = false
showConsoleLogs = true
shellCmdPre = ""
shellCmdPost = ""
autoRun = false
isModule = false

[Start application.commands]
restartable = true
isVisible = true
supportShell = false
isBackspace = false
isCtrlc = false
isKeyStrokes = false
cmd = [
  "gunicorn", 
  "main:app", 
  "-k", "gevent", 
  "-w", "4", 
  "--timeout", "300", 
  "--bind", "0.0.0.0:5000",
  "--reuse-port", 
  "--reload"
]
"""
    
    write_file(".replit.workflow", workflow_content)
    logger.info("Created .replit.workflow with correct gunicorn configuration")
    
    # Update .replit file if it exists
    replit_path = ".replit"
    if os.path.exists(replit_path):
        replit_content = read_file(replit_path)
        if replit_content:
            # Update deployment run command
            if "[deployment]" in replit_content:
                deploy_pattern = r'(\[deployment\]\s*.*?\s*run\s*=\s*\[)[^\]]*(\])'
                new_replit = re.sub(
                    deploy_pattern, 
                    r'\1"gunicorn", "main:app", "-k", "gevent", "-w", "4", "--timeout", "300", "--bind", "0.0.0.0:5000"\2', 
                    replit_content, 
                    flags=re.DOTALL
                )
                
                if new_replit != replit_content:
                    if backup_file(replit_path):
                        write_file(replit_path, new_replit)
                        logger.info("Updated gunicorn configuration in .replit file")

def main():
    """Main function to run all fixes"""
    logger.info("Starting deployment fixes...")
    
    app_py_path = "app.py"
    main_py_path = "main.py"
    
    # Run all fixes
    fix_sqlalchemy_initialization(app_py_path, main_py_path)
    fix_azure_blob_storage(app_py_path)
    fix_gunicorn_config()
    
    logger.info("Fixes completed. Please restart the application and try deploying again.")

if __name__ == "__main__":
    main()