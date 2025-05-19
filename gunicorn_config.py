"""
Gunicorn configuration file for Replit deployment

This configuration is designed to work well with Replit's deployment system,
providing appropriate timeouts, worker settings, and logging options.
"""

import os
import multiprocessing

# Bind to the IP and port that Replit expects
bind = "0.0.0.0:5000"

# Worker configuration
workers = 2  # Reduced from 4 to avoid memory limits on Replit
worker_class = "gevent"  # Use gevent for async support
threads = 2

# Timeouts (in seconds)
timeout = 120  # Reduced from 300 to be more responsive
graceful_timeout = 30
keepalive = 5

# Logging
errorlog = "-"  # Log to stderr
accesslog = "-"  # Log to stdout
loglevel = "info"

# Set application module
wsgi_app = "wsgi:app"  # Use the wsgi.py entry point

# Preload the application for better performance
preload_app = True

# Forward allowed IPs
forwarded_allow_ips = '*'

# Security
limit_request_line = 4096
limit_request_fields = 100

# Use a timeout hook for additional resilience
def timeout_worker(worker):
    """Timeout hook to handle worker timeouts more gracefully"""
    worker.log.critical("WORKER TIMEOUT (pid: %s)", worker.pid)
    worker.alive = False