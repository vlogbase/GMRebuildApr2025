"""
Test script for verifying Gunicorn configuration for Replit deployment

This script tries to start the application using the same Gunicorn command
that Replit would use for deployment, helping diagnose any issues.
"""

import os
import sys
import subprocess
import logging
import time
import requests
import signal
import atexit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("deployment-test")

# Gunicorn command from .replit deployment section
GUNICORN_COMMAND = "gunicorn main:app -k gevent -w 4 --timeout 300 --bind 0.0.0.0:5000"

def run_gunicorn_test():
    """Run Gunicorn with the deployment configuration and test health endpoints"""
    
    # Log environment information
    logger.info(f"Python version: {sys.version}")
    
    # Print Redis environment variables (without passwords)
    redis_host = os.environ.get('REDIS_HOST', 'Not configured')
    redis_port = os.environ.get('REDIS_PORT', 'Not configured')
    ssl_enabled = os.environ.get('REDIS_SSL', 'Not configured')
    
    logger.info(f"Redis configuration: host={redis_host}, port={redis_port}, ssl={ssl_enabled}")
    
    try:
        # Start Gunicorn as a subprocess
        logger.info(f"Starting Gunicorn with command: {GUNICORN_COMMAND}")
        process = subprocess.Popen(
            GUNICORN_COMMAND.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Register cleanup function to ensure process is terminated
        @atexit.register
        def cleanup():
            if process.poll() is None:
                logger.info("Terminating Gunicorn process")
                process.send_signal(signal.SIGTERM)
                process.wait(timeout=5)
                
        # Wait a bit for Gunicorn to start
        logger.info("Waiting for Gunicorn to start (5 seconds)...")
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            logger.error(f"Gunicorn process exited prematurely with code {process.returncode}")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            return False
            
        # Test health endpoints
        endpoints = ['/', '/health', '/healthz']
        
        for endpoint in endpoints:
            url = f"http://localhost:5000{endpoint}"
            try:
                logger.info(f"Testing health endpoint: {url}")
                response = requests.get(url, timeout=5)
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response body: {response.text[:100]}...")
                
                if response.status_code == 200:
                    logger.info(f"✅ Health check passed for {endpoint}")
                else:
                    logger.warning(f"❌ Health check failed for {endpoint}")
            except requests.RequestException as e:
                logger.error(f"Error accessing {url}: {e}")
                
        # Check Gunicorn process output for errors
        stdout_data, stderr_data = b"", b""
        try:
            stdout_data, stderr_data = process.communicate(timeout=0.1)
        except subprocess.TimeoutExpired:
            # Process is still running, which is expected
            pass
            
        # Log any error output
        if stderr_data:
            logger.warning(f"Gunicorn stderr output: {stderr_data.decode('utf-8')}")
            
        # Test completed successfully
        logger.info("Gunicorn deployment test completed")
        return True
            
    except Exception as e:
        logger.error(f"Error running Gunicorn test: {e}")
        return False
    finally:
        # Ensure cleanup
        if 'process' in locals() and process.poll() is None:
            logger.info("Stopping Gunicorn")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                
if __name__ == "__main__":
    success = run_gunicorn_test()
    sys.exit(0 if success else 1)