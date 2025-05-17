"""
Standalone test script for the model fallback confirmation feature.

This script doesn't depend on the full app, but demonstrates how the feature works.
"""
import os
import logging
import tempfile
from flask import Flask, render_template, jsonify, request, session

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_app():
    """Create a minimal test Flask app"""
    app = Flask(__name__)
    app.secret_key = 'test_secret_key'
    
    # Create basic routes for testing
    @app.route('/')
    def index():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Model Fallback Test</title>
            <meta name="csrf-token" content="test-csrf-token">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .card { border: 1px solid #ccc; border-radius: 5px; padding: 20px; max-width: 600px; margin: 0 auto; }
                button { padding: 10px 15px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
                #results { margin-top: 20px; padding: 10px; background: #f5f5f5; border-radius: 4px; min-height: 100px; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Model Fallback Confirmation Test</h1>
                <p>This page tests the model fallback confirmation dialog.</p>
                <button id="testButton">Test Fallback Dialog</button>
                <div id="results">Results will appear here...</div>
            </div>
            
            <script>
                // Mock the ModelFallback module for testing
                window.ModelFallback = {
                    showFallbackDialog: function(requestedModel, fallbackModel, message, fallbackId) {
                        console.log('ModelFallback.showFallbackDialog called with:', {
                            requestedModel, fallbackModel, message, fallbackId
                        });
                        
                        alert(`Model Fallback Dialog would show here:
                        
Requested model: ${requestedModel}
Fallback model: ${fallbackModel}
Message: ${message}
                        
This is a simulation of the dialog that would appear when a model is unavailable.`);
                        
                        // Simulate user accepting the fallback
                        if (confirm('Would you like to accept the fallback model?')) {
                            console.log('User accepted fallback');
                            if (typeof window.sendChatMessageWithFallback === 'function') {
                                window.sendChatMessageWithFallback(message, fallbackId);
                            } else {
                                console.error('sendChatMessageWithFallback function not available');
                            }
                        } else {
                            console.log('User rejected fallback');
                        }
                    },
                    getUserAutoFallbackPreference: function() {
                        return false; // Always show confirmation in test
                    }
                };
                
                // Mock the sendChatMessageWithFallback function
                window.sendChatMessageWithFallback = function(message, fallbackId) {
                    console.log('sendChatMessageWithFallback called with:', { message, fallbackId });
                    document.getElementById('results').innerHTML = `
                        <p><strong>Message sent with fallback model:</strong></p>
                        <p>Message: ${message}</p>
                        <p>Fallback Model: ${fallbackId}</p>
                    `;
                };
                
                // Test button event handler
                document.getElementById('testButton').addEventListener('click', function() {
                    fetch('/api/test-fallback', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                        },
                        body: JSON.stringify({
                            model: 'anthropic/claude-3-haiku'
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.type === 'model_fallback') {
                            // Create a simulated chat message to trigger the fallback dialog
                            const fallbackEvent = new CustomEvent('modelFallbackEvent', {
                                detail: {
                                    requestedModel: data.requested_model,
                                    fallbackModel: data.fallback_model,
                                    originalModelId: data.original_model_id,
                                    fallbackModelId: data.fallback_model_id,
                                    message: "This is a test message",
                                    reason: data.reason
                                }
                            });
                            
                            document.dispatchEvent(fallbackEvent);
                        } else {
                            document.getElementById('results').textContent = 'Error: Unexpected response from server';
                        }
                    })
                    .catch(error => {
                        document.getElementById('results').textContent = 'Error: ' + error.message;
                    });
                });
                
                // Event listener for model fallback events
                document.addEventListener('modelFallbackEvent', function(event) {
                    console.log('Model fallback event received:', event.detail);
                    
                    // Extract data from the event
                    const requestedModel = event.detail.requestedModel;
                    const fallbackModel = event.detail.fallbackModel;
                    const message = event.detail.message || "Test message";
                    const fallbackModelId = event.detail.fallbackModelId || "";
                    
                    // Check if we have the ModelFallback module
                    if (typeof window.ModelFallback !== 'undefined' && 
                        typeof window.ModelFallback.showFallbackDialog === 'function') {
                        
                        console.log("Using ModelFallback dialog for confirmation");
                        
                        // Check if auto-fallback is enabled in user preferences
                        const autoFallbackEnabled = window.ModelFallback.getUserAutoFallbackPreference();
                        
                        if (autoFallbackEnabled) {
                            console.log("Auto-fallback is enabled, proceeding without confirmation");
                            // Automatically proceed with fallback model
                            sendChatMessageWithFallback(message, fallbackModelId);
                        } else {
                            // Show confirmation dialog
                            window.ModelFallback.showFallbackDialog(
                                requestedModel,
                                fallbackModel,
                                message,
                                fallbackModelId
                            );
                        }
                    } else {
                        console.error("ModelFallback module not available");
                        alert(`Model ${requestedModel} is unavailable. Please select a different model.`);
                    }
                });
            </script>
        </body>
        </html>
        """
    
    @app.route('/api/test-fallback', methods=['POST'])
    def test_fallback_api():
        """Simulate a model fallback situation for testing"""
        try:
            data = request.json
            requested_model = data.get('model', 'anthropic/claude-3-haiku')
            requested_name = requested_model.split('/')[-1].replace('-', ' ').title()
            
            # Simulate fallback to Gemini Flash
            fallback_model_id = 'google/gemini-flash:free'
            fallback_model_name = 'Gemini Flash'
            
            # Return a fallback notification
            return jsonify({
                'type': 'model_fallback',
                'requested_model': requested_name,
                'fallback_model': fallback_model_name,
                'original_model_id': requested_model,
                'fallback_model_id': fallback_model_id,
                'reason': 'Model unavailable for testing purposes'
            })
        except Exception as e:
            logger.error(f"Error in test_fallback_api: {e}")
            return jsonify({
                'error': str(e)
            }), 500
    
    return app

def run():
    """Run the test app for model fallback confirmation"""
    app = create_test_app()
    logger.info("=" * 80)
    logger.info("MODEL FALLBACK CONFIRMATION TEST")
    logger.info("=" * 80)
    logger.info("Test the model fallback confirmation feature by:")
    logger.info("1. Navigate to http://localhost:5000")
    logger.info("2. Click the 'Test Fallback Dialog' button to simulate a model fallback")
    logger.info("=" * 80)
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()