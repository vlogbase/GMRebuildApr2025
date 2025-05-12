"""
Main entry point for Replit deployment.
This file is used by Replit for deployments.
"""
import sys
import os

# Use this as a simple entry point that calls our actual app workflow
if __name__ == "__main__":
    # Make sure we use port 3000 for Replit deployments
    if "PORT" not in os.environ:
        os.environ["PORT"] = "3000"
    
    try:
        # Execute the app_workflow.py file
        from app_workflow import run
        run()
    except Exception as e:
        print(f"Error starting the application: {e}")
        sys.exit(1)