"""
Simple test script to add a test route to the main app
that demonstrates the model fallback confirmation feature.
"""
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to the path for importing the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app
from app import app
from flask import jsonify, render_template, request, Response, stream_with_context
import json

@app.route('/test-fallback')
def test_fallback_page():
    """Test page for model fallback confirmation"""
    return render_template('index.html', testMode=True)

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

if __name__ == '__main__':
    # Add the test route to the app
    logger.info("Starting app with test fallback route added")
    logger.info("Test URL: http://localhost:5000/test-fallback")
    
    # Run the app with the test route
    app.run(host='0.0.0.0', port=5000, debug=True)