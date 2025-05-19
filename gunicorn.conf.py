"""
Gunicorn configuration file
"""

# Performance optimizations
workers = 2  # Reduce the number of workers to avoid memory issues
worker_class = 'gevent'  # Use gevent for better async handling
worker_connections = 1000
timeout = 120  # Increase timeout to handle longer requests
graceful_timeout = 30

# Memory optimizations
max_requests = 1000  # Restart workers after handling this many requests
max_requests_jitter = 200  # Add jitter to prevent all workers from restarting at the same time

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'  # Log errors to stdout
loglevel = 'info'

# Bind to appropriate host and port
bind = '0.0.0.0:3000'  # Ensure this matches the expected deployment port

# Deployment specific settings
preload_app = True  # Preload app to share application memory
forwarded_allow_ips = '*'  # Trust X-Forwarded-* headers