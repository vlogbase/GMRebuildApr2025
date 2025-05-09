"""
Simple script to run the Flask application for testing admin access functionality.
"""

import os
import sys
import subprocess

def main():
    """
    Run the Flask application with admin access enabled for testing.
    This is a simple wrapper around admin_app_workflow.py.
    """
    # Set environment variables for testing
    os.environ['ADMIN_EMAILS'] = 'andy@sentigral.com,test@example.com'
    os.environ['FLASK_ENV'] = 'development'
    
    # Clear the console
    os.system('clear')
    
    # Print header
    print("\n===== Admin Dashboard Testing =====")
    print("Running Flask application with admin access enabled...")
    print("Environment:")
    print(f"  ADMIN_EMAILS: {os.environ.get('ADMIN_EMAILS')}")
    print(f"  FLASK_ENV: {os.environ.get('FLASK_ENV')}")
    print("==================================\n")
    
    # Run the admin app workflow
    try:
        subprocess.run([sys.executable, "admin_app_workflow.py", "run"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running admin app workflow: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAdmin test interrupted by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()