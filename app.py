import os
import logging
import json
import requests
from flask import Flask, render_template, request, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, current_user

# Check if we should enable advanced memory features
ENABLE_MEMORY_SYSTEM = os.environ.get('ENABLE_MEMORY_SYSTEM', 'false').lower() == 'true'

if ENABLE_MEMORY_SYSTEM:
    try:
        from memory_integration import save_message_with_memory, enrich_prompt_with_memory
        logging.info("Advanced memory system enabled")
    except ImportError as e:
        logging.warning(f"Failed to import memory integration: {e}")
        ENABLE_MEMORY_SYSTEM = False

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# SQLAlchemy setup
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "developmentsecretkey")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy with the app
db.init_app(app)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# OpenRouter model mappings
OPENROUTER_MODELS = {
    "gemini-1.5-pro": "google/gemini-pro-1.5",  # Updated to correct ID
    "claude-3-sonnet": "anthropic/claude-3-sonnet",
    "mistral-large": "mistralai/mistral-large",
    "gpt-4o": "openai/gpt-4o",
    "sonar-pro": "anthropic/claude-3-opus",  # "Sonar Pro" maps to Claude 3 Opus
    "free-gemini": "google/gemma-3-27b-it:free"  # Free tier Gemini model
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations for the current user or create a new conversation"""
    # If user is logged in, get their conversations
    # Otherwise return a limited set of conversations or empty list
    try:
        from models import Conversation, Message
        
        # For now, just return a list of dummy conversations
        # In a real implementation, you would filter by current_user.id
        conversations = []
        
        # Create a test conversation if none exist
        if len(conversations) == 0:
            # For now, create a demo conversation
            conversation = Conversation(title="Demo Conversation")
            db.session.add(conversation)
            db.session.commit()
            
            conversations = [{"id": conversation.id, "title": conversation.title}]
        
        return Response(json.dumps({"conversations": conversations}), content_type='application/json')
    except Exception as e:
        logger.exception("Error getting conversations")
        return Response(json.dumps({"error": str(e)}), content_type='application/json', status=500)


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
        conversation_id = data.get('conversation_id', None)
        
        # Import models for database operations
        from models import Conversation, Message
        
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
        
        # Prepare messages array with a detailed system prompt
        system_message = (
            "You are a helpful assistant at GloriaMundo, an advanced AI chat platform. "
            "Provide detailed, accurate, and helpful responses to user queries. "
            "Write in a conversational yet professional tone. "
            "If you don't know something, say so rather than making up information. "
            "Format responses with clear structure using paragraphs, lists, and emphasis when appropriate."
        )
        messages = [{'role': 'system', 'content': system_message}]
        
        # Get or create a conversation
        conversation = None
        if conversation_id:
            conversation = Conversation.query.get(conversation_id)
        
        if not conversation:
            # Create a new conversation with a title based on the first message
            title = user_message[:50] + "..." if len(user_message) > 50 else user_message
            conversation = Conversation(title=title)
            db.session.add(conversation)
            db.session.commit()
            conversation_id = conversation.id
        
        # Save the user message to the database
        user_db_message = Message(
            conversation_id=conversation.id,
            role='user',
            content=user_message
        )
        db.session.add(user_db_message)
        db.session.commit()
        
        # Save user message to memory system if enabled
        if ENABLE_MEMORY_SYSTEM:
            try:
                # The current user ID (use conversation ID if user not logged in)
                memory_user_id = str(current_user.id) if current_user and current_user.is_authenticated else f"anonymous_{conversation_id}"
                
                # Asynchronously save to memory
                save_message_with_memory(
                    session_id=str(conversation_id),
                    user_id=memory_user_id,
                    role='user',
                    content=user_message
                )
            except Exception as e:
                logger.error(f"Error saving user message to memory: {e}")
        
        # Add message history if available from the request
        if message_history:
            messages.extend(message_history)
        else:
            # If no history in request, load from database
            db_messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
            for msg in db_messages:
                messages.append({'role': msg.role, 'content': msg.content})
        
        # Add the current user message
        messages.append({'role': 'user', 'content': user_message})
        
        # Enrich with memory if enabled
        if ENABLE_MEMORY_SYSTEM:
            try:
                # The current user ID (use conversation ID if user not logged in)
                memory_user_id = str(current_user.id) if current_user and current_user.is_authenticated else f"anonymous_{conversation_id}"
                
                # Enrich the messages with relevant memory
                original_message_count = len(messages)
                messages = enrich_prompt_with_memory(
                    session_id=str(conversation_id),
                    user_id=memory_user_id,
                    user_message=user_message,
                    conversation_history=messages
                )
                
                if len(messages) > original_message_count:
                    logger.info(f"Added {len(messages) - original_message_count} context messages from memory system")
            except Exception as e:
                logger.error(f"Error enriching with memory: {e}")
                # Continue without memory enrichment if it fails
        
        logger.debug(f"Sending message history with {len(messages)} messages")
        
        # Prepare payload for OpenRouter
        payload = {
            'model': openrouter_model,
            'messages': messages,
            'stream': True
        }
        
        logger.debug(f"Sending request to OpenRouter with model: {openrouter_model}")
        
        # Buffer to collect the assistant's response
        assistant_response = []
        
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
                                # Save the complete assistant response to the database
                                full_response = ''.join(assistant_response)
                                assistant_db_message = Message(
                                    conversation_id=conversation_id,
                                    role='assistant',
                                    content=full_response,
                                    model=model_id
                                )
                                db.session.add(assistant_db_message)
                                db.session.commit()
                                
                                # Save to memory system if enabled
                                if ENABLE_MEMORY_SYSTEM:
                                    try:
                                        # The current user ID (use conversation ID if user not logged in)
                                        memory_user_id = str(current_user.id) if current_user and current_user.is_authenticated else f"anonymous_{conversation_id}"
                                        
                                        # Asynchronously save to memory
                                        save_message_with_memory(
                                            session_id=str(conversation_id),
                                            user_id=memory_user_id,
                                            role='assistant',
                                            content=full_response
                                        )
                                    except Exception as e:
                                        logger.error(f"Error saving to memory: {e}")
                                
                                # Send the DONE marker to the client
                                yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"
                                continue
                            
                            # Parse the data as JSON
                            json_data = json.loads(sse_data)
                            
                            # Extract the content from the choices
                            if 'choices' in json_data and len(json_data['choices']) > 0:
                                choice = json_data['choices'][0]
                                
                                # Handle different response formats
                                content = None
                                if 'delta' in choice and 'content' in choice['delta']:
                                    # OpenAI-like format
                                    content = choice['delta']['content']
                                elif 'delta' in choice and choice['delta'].get('content', None) is None:
                                    # Empty delta content, just continue
                                    continue
                                elif 'text' in choice:
                                    # Some models might use 'text' directly
                                    content = choice['text']
                                elif 'content' in choice:
                                    # Some models might include content directly
                                    content = choice['content']
                                
                                if content:
                                    # Add content to the buffer
                                    assistant_response.append(content)
                                    
                                    # Send content to the client
                                    yield f"data: {json.dumps({'content': content, 'conversation_id': conversation_id})}\n\n"
                                    logger.debug(f"Streamed content chunk: {content[:20]}...")
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
