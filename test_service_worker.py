"""
Simple test script for the service worker functionality

This script serves the service worker and manifest files to test
the caching improvements with better error diagnostics.
"""

import os
import logging
import sys
from flask import Flask, send_from_directory, render_template_string

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("service-worker-test")

# Create a simple Flask app for testing
app = Flask(__name__)

@app.route('/')
def index():
    """Serve a simple test page that registers the service worker"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Service Worker Test</title>
        <link rel="manifest" href="/static/manifest/manifest.json">
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        <h1>Service Worker Test</h1>
        <p>This page tests the service worker registration and caching.</p>
        <p>Check the console for details on service worker registration and caching.</p>
        
        <script>
            // Register service worker
            if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                    navigator.serviceWorker.register('/static/js/service-worker.js')
                        .then(function(registration) {
                            console.log('Service Worker registered with scope:', registration.scope);
                            
                            // Listen for messages from the service worker
                            navigator.serviceWorker.addEventListener('message', function(event) {
                                console.log('Message from Service Worker:', event.data);
                            });
                        })
                        .catch(function(error) {
                            console.error('Service Worker registration failed:', error);
                        });
                });
            } else {
                console.warn('Service workers are not supported in this browser.');
            }
            
            // Log service worker readiness
            if (navigator.serviceWorker.controller) {
                console.log('This page is controlled by a service worker');
            } else {
                console.log('This page is not yet controlled by a service worker.');
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

def run():
    """Run the test Flask application"""
    logger.info("Starting Service Worker test application")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()