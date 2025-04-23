"""
Workflow runner for the Replit environment.
This automatically handles the workflow tasks defined in .replit.
"""
import os
import subprocess
import sys

def run_app():
    """Run the Flask application with gunicorn."""
    cmd = [
        "gunicorn", 
        "main:app", 
        "-k", "gevent", 
        "-w", "1", 
        "--timeout", "300",
        "--bind", "0.0.0.0:5000",
        "--reload"
    ]
    subprocess.run(cmd)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run_app()
    else:
        print("Usage: python workflow.py run")