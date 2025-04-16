"""
Helper script to start the server with gevent workers
"""
import os
import subprocess
import sys

# Determine if we're in a production environment
is_prod = os.environ.get("PRODUCTION", "false").lower() == "true"
workers = 4 if is_prod else 2
timeout = 300

print(f"Starting server with {workers} gevent workers and {timeout}s timeout...")

# Command to run with gevent worker
cmd = [
    "gunicorn",
    "main:app",
    "-k", "gevent",
    "-w", str(workers),
    "--timeout", str(timeout),
    "--bind", "0.0.0.0:5000",
    "--reuse-port",
]

# Add --reload in development mode
if not is_prod:
    cmd.append("--reload")

# Print the command being run
print(f"Running: {' '.join(cmd)}")

# Execute the command
try:
    process = subprocess.run(cmd)
    sys.exit(process.returncode)
except KeyboardInterrupt:
    print("\nShutting down server...")
    sys.exit(0)
except Exception as e:
    print(f"Error starting server: {e}")
    sys.exit(1)