"""
Test script that runs the app with minimal modifications needed for model fallback confirmation
"""
import os
import sys
import logging
from flask import Flask, request, jsonify, Response, stream_with_context, render_template
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the Flask app but don't run it
from app import app, db

# Add a route to test the model fallback notification
@app.route('/api/test-fallback', methods=['POST'])
def test_fallback_api():
    """Test API route that always returns a fallback needed response"""
    data = request.json
    logger.info(f"Test fallback request received: {data}")
    
    # Extract the requested model
    model_id = data.get('model', 'anthropic/claude-3-haiku-20240307')
    
    def generate_fallback_notification():
        """Generate a model fallback notification event"""
        fallback_json = json.dumps({
            'type': 'model_fallback',
            'requested_model': 'Claude 3 Haiku',
            'fallback_model': 'GPT-4o',
            'original_model_id': model_id,
            'fallback_model_id': 'openai/gpt-4o-2024-05-13'
        })
        yield f'data: {fallback_json}\n\n'
    
    return Response(
        stream_with_context(generate_fallback_notification()),
        mimetype='text/event-stream'
    )

@app.route('/test-fallback-page')
def test_fallback_page():
    """Dedicated test page for model fallback confirmation feature"""
    return render_template('test_fallback.html')

# Helper route that displays the model_fallback.js content
@app.route('/debug/model-fallback-js')
def debug_model_fallback_js():
    """View the contents of model_fallback.js for debugging"""
    try:
        with open('static/js/model_fallback.js', 'r') as f:
            js_content = f.read()
        
        return render_template('debug_template.html', 
                               title='model_fallback.js content',
                               content=js_content)
    except Exception as e:
        return jsonify({'error': f'Error reading file: {str(e)}'})

if __name__ == '__main__':
    # Add the test route to the app
    logger.info("Starting app with test fallback route added")
    logger.info("Test URLs:")
    logger.info("http://localhost:5000/test-fallback-page")
    logger.info("http://localhost:5000/debug/model-fallback-js")
    
    # Run the app with the test route
    app.run(host='0.0.0.0', port=5000, debug=True)