"""
A minimal script to test the RAG document indicator display in the frontend.
"""
import os
import logging
import json
from flask import Flask, render_template, Response, stream_with_context, request

# Setup more detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a minimal Flask app for testing
app = Flask(__name__)

@app.route('/')
def index():
    """Render the chat interface template"""
    logger.info("Rendering index template")
    return render_template('index.html')

@app.route('/api/models', methods=['GET'])
def get_models():
    """Return a minimal list of models for the test"""
    models = [
        {
            "id": "anthropic/claude-3-opus-20240229",
            "name": "Claude 3 Opus",
            "description": "Most powerful Claude model for complex tasks",
            "pricing": {"prompt": 15, "completion": 75},
            "capabilities": ["vision", "tools"]
        }
    ]
    logger.info("Returning models list")
    return {"models": models}

@app.route('/api/model-pricing', methods=['GET'])
def get_model_pricing():
    """Return pricing info for models"""
    logger.info("Returning model pricing")
    return {
        "anthropic/claude-3-opus-20240229": {"prompt": 15, "completion": 75}
    }

@app.route('/api/chat', methods=['POST'])
def test_chat():
    """
    Test endpoint that simulates a chat response with the RAG indicator enabled.
    This simplifies testing by always setting using_documents=True in the metadata.
    """
    logger.debug("Received chat request: %s", request.json if request.is_json else "No JSON data")
    
    def generate():
        logger.debug("Starting SSE response generation")
        
        # Send a sample message chunk by chunk to simulate streaming
        message_text = "This is a test response that includes RAG document information. The important thing about RAG is that it uses your documents to provide more relevant information."
        
        # Split the message into smaller chunks to simulate streaming
        chunks = [message_text[i:i+20] for i in range(0, len(message_text), 20)]
        
        for chunk in chunks:
            logger.debug("Sending message chunk: %s", chunk)
            yield f"data: {json.dumps({'type': 'message', 'message': chunk})}\n\n"
        
        # Send metadata with using_documents flag set to True
        metadata = {
            'id': '123456',
            'model_id_used': 'anthropic/claude-3-opus-20240229',
            'prompt_tokens': 100,
            'completion_tokens': 150,
            'using_documents': True,
            'document_sources': ['Document 1.pdf', 'Document 2.docx']
        }
        
        logger.debug("Sending metadata with using_documents=True: %s", metadata)
        yield f"data: {json.dumps({'type': 'metadata', 'metadata': metadata})}\n\n"
        
        # Signal done
        logger.debug("Sending done signal")
        yield f"data: {json.dumps({'type': 'done', 'done': True, 'conversation_id': '789'})}\n\n"
    
    return Response(stream_with_context(generate()), content_type='text/event-stream')

@app.route('/api/csrf-test', methods=['POST'])
def csrf_test():
    """Test endpoint for CSRF protection"""
    return {"success": True}

@app.route('/api/preferences', methods=['GET'])
def get_preferences():
    """Return default preferences"""
    return {
        "preset_models": {
            "default": "anthropic/claude-3-opus-20240229",
            "preset1": "anthropic/claude-3-opus-20240229",
            "preset2": "anthropic/claude-3-opus-20240229",
            "preset3": "anthropic/claude-3-opus-20240229"
        }
    }

if __name__ == '__main__':
    logger.info("Starting test server on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=True)