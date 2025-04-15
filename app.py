import os
import logging
import json
import requests
from flask import Flask, render_template, request, Response, stream_with_context

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# OpenRouter model mappings
OPENROUTER_MODELS = {
    "gemini-1.5-pro": "google/gemini-1.5-pro-latest",
    "claude-3-sonnet": "anthropic/claude-3-sonnet",
    "mistral-large": "mistralai/mistral-large-latest",
    "gpt-4o": "openai/gpt-4o",
    "sonar-pro": "anthropic/claude-3-opus",  # Best guess for "Sonar Pro"
    "free-gemini": "google/gemini-1.0-pro"   # Free tier model
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint to handle chat messages and stream responses from OpenRouter
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        model_id = data.get('model', 'gemini-1.5-pro')
        message_history = data.get('history', [])
        
        # Get the corresponding OpenRouter model ID
        openrouter_model = OPENROUTER_MODELS.get(model_id, OPENROUTER_MODELS['gemini-1.5-pro'])
        
        # Get API key from environment
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            logger.error("OPENROUTER_API_KEY not found in environment variables")
            return Response(json.dumps({"error": "API key not configured"}), 
                           content_type='application/json', status=500)
        
        # Prepare headers for OpenRouter API
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': request.headers.get('Referer', 'https://gloriamundo.com')
        }
        
        # Prepare messages array
        messages = [{'role': 'system', 'content': 'You are a helpful assistant at GloriaMundo.'}]
        
        # Add message history if available
        if message_history:
            messages.extend(message_history)
        
        # Add the current user message
        messages.append({'role': 'user', 'content': user_message})
        
        logger.debug(f"Sending message history with {len(messages)} messages")
        
        # Prepare payload for OpenRouter
        payload = {
            'model': openrouter_model,
            'messages': messages,
            'stream': True
        }
        
        logger.debug(f"Sending request to OpenRouter with model: {openrouter_model}")
        
        # Stream the response using requests
        def generate():
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=payload,
                stream=True
            )
            
            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                yield f"data: {json.dumps({'error': f'API Error: {response.status_code}'})}\n\n"
                return
            
            # Process the streaming response
            for line in response.iter_lines():
                if line:
                    # Skip keep-alive lines
                    if line.strip() == b'':
                        continue
                    
                    line_text = line.decode('utf-8')
                    
                    # Handle SSE format from OpenRouter
                    if line_text.startswith('data: '):
                        try:
                            sse_data = line_text[6:]  # Remove 'data: ' prefix
                            
                            # Check for [DONE] marker
                            if sse_data.strip() == '[DONE]':
                                yield f"data: [DONE]\n\n"
                                continue
                            
                            # Parse the data as JSON
                            json_data = json.loads(sse_data)
                            
                            # Extract the content from the choices
                            if 'choices' in json_data and len(json_data['choices']) > 0:
                                choice = json_data['choices'][0]
                                if 'delta' in choice and 'content' in choice['delta']:
                                    content = choice['delta']['content']
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON decode error: {e}")
                            logger.error(f"Problematic line: {line_text}")
                            yield f"data: {json.dumps({'error': 'JSON parsing error'})}\n\n"
        
        return Response(stream_with_context(generate()), content_type='text/event-stream')
    
    except Exception as e:
        logger.exception("Error in chat endpoint")
        return Response(json.dumps({"error": str(e)}), content_type='application/json', status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
