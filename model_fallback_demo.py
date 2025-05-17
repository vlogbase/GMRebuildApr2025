"""
Simple standalone demo of the model fallback confirmation feature.
This avoids the indentation issues in the main app.py file.
"""
import os
import sys
import logging
from flask import Flask, render_template, jsonify, request, Response, stream_with_context
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a simple Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback-demo-secret-key")

# Add a route for the test page
@app.route('/')
def index():
    """Main demo page"""
    return render_template('test_fallback.html')

# API endpoint to demonstrate fallback response
@app.route('/api/demo-fallback', methods=['POST'])
def demo_fallback():
    """Generate a model fallback event"""
    data = request.json
    logger.info(f"Demo fallback request received: {data}")
    
    model_id = data.get('model', 'anthropic/claude-3-haiku-20240307')
    
    def generate_fallback_notification():
        """Generate a model fallback notification event"""
        try:
            fallback_json = json.dumps({
                'type': 'model_fallback',
                'requested_model': 'Claude 3 Haiku',
                'fallback_model': 'GPT-4o',
                'original_model_id': model_id,
                'fallback_model_id': 'openai/gpt-4o-2024-05-13'
            })
            yield f'data: {fallback_json}\n\n'
        except Exception as e:
            logger.error(f"Error generating fallback notification: {e}")
            error_json = json.dumps({
                'type': 'error',
                'error': 'Failed to generate fallback notification'
            })
            yield f'data: {error_json}\n\n'
    
    return Response(
        stream_with_context(generate_fallback_notification()),
        mimetype='text/event-stream'
    )

# Endpoint to handle chat settings
@app.route('/api/user/chat_settings', methods=['GET', 'POST'])
def chat_settings():
    """Get or update chat settings including auto_fallback_enabled"""
    if request.method == 'POST':
        data = request.json
        auto_fallback = data.get('auto_fallback_enabled', False)
        
        # In a real app, this would update the database
        # For demo purposes, we'll just return success
        logger.info(f"Setting auto_fallback_enabled to {auto_fallback}")
        
        return jsonify({
            'success': True,
            'settings': {
                'auto_fallback_enabled': auto_fallback
            }
        })
    else:
        # In a real app, this would query the database
        # For demo purposes, we'll just return a default value
        return jsonify({
            'success': True,
            'settings': {
                'auto_fallback_enabled': False
            }
        })

# Create a simple page to show the model_fallback.js content
@app.route('/debug/model-fallback-js')
def debug_model_fallback_js():
    """View the contents of model_fallback.js"""
    try:
        with open('static/js/model_fallback.js', 'r') as f:
            js_content = f.read()
        
        return render_template('debug_template.html', 
                              title='model_fallback.js content',
                              content=js_content)
    except Exception as e:
        return jsonify({'error': f'Error reading file: {str(e)}'})

if __name__ == '__main__':
    logger.info("Starting model fallback demo")
    logger.info("Test URL: http://localhost:5000/")
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)