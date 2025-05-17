"""
Simple test script to verify the model fallback confirmation dialog functionality.
This will simulate the API response for model fallback and test the dialog handling.
"""
import os
import logging
import json
from flask import Flask, Response, stream_with_context, render_template, request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a simple test app
app = Flask(__name__)

@app.route('/')
def index():
    """Render the test page with chat interface"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Simulate a chat response with model fallback"""
    data = request.json
    logger.info(f"Chat request received: {data}")
    
    # Extract the requested model
    model_id = data.get('model', '')
    message = data.get('message', '')
    
    # Check if this is the model we want to simulate as unavailable
    if model_id == 'anthropic/claude-3-haiku-20240307':
        logger.info(f"Simulating unavailable model: {model_id}")
        
        def generate_fallback_notification():
            fallback_json = json.dumps({
                'type': 'model_fallback',
                'requested_model': 'Claude 3 Haiku',
                'fallback_model': 'GPT-4o',
                'original_model_id': 'anthropic/claude-3-haiku-20240307',
                'fallback_model_id': 'openai/gpt-4o-2024-05-13'
            })
            yield f'data: {fallback_json}\n\n'
        
        return Response(
            stream_with_context(generate_fallback_notification()),
            mimetype='text/event-stream'
        )
    
    # For any other model, return a normal response
    def generate_normal_response():
        # Send content chunks
        content_json = json.dumps({
            'type': 'content',
            'content': f"This is a test response from model {model_id}.\n\nYour message was: {message}"
        })
        yield f'data: {content_json}\n\n'
        
        # Send done event
        done_json = json.dumps({
            'type': 'done',
            'conversation_id': '123456'
        })
        yield f'data: {done_json}\n\n'
    
    return Response(
        stream_with_context(generate_normal_response()),
        mimetype='text/event-stream'
    )

@app.route('/api/user/chat_settings', methods=['GET', 'POST'])
def chat_settings():
    """Handle user chat settings API"""
    if request.method == 'POST':
        data = request.json
        logger.info(f"Received chat settings update: {data}")
        auto_fallback = data.get('auto_fallback_enabled', False)
        return {'success': True, 'settings': {'auto_fallback_enabled': auto_fallback}}
    else:
        # For GET, return default settings
        return {'success': True, 'settings': {'auto_fallback_enabled': False}}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\nTest server running on http://localhost:{port}")
    print("Test the model fallback confirmation dialog by:")
    print("1. Select 'Claude 3 Haiku' model in the UI")
    print("2. Send a message to see the fallback confirmation dialog")
    print("3. Test 'Accept', 'Reject', and the 'Always use fallback' checkbox\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)