"""
Workflow functions for Replit workflow integration.
"""
import sys
import subprocess

def run(workflow_name=None):
    """Run a script based on the workflow name."""
    print(f"Running {workflow_name or 'default'} workflow")
    
    if workflow_name == "favicon-test":
        # Run the web server script for testing favicons
        subprocess.run(["python", "web_server.py"])
    else:
        # Default execution
        subprocess.run(["python", "app.py"])