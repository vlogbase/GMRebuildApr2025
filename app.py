import os
import logging
import json
import requests
import uuid
import time
import base64
import secrets
from flask import Flask, render_template, request, Response, session, stream_with_context, jsonify, abort, url_for, redirect, flash
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
    "gemini-1.5-pro": "google/gemini-2.5-pro-preview-03-25",
    "claude-3-sonnet": "anthropic/claude-3.7-sonnet",
    "mistral-large": "mistralai/mistral-large",
    "gpt-4o": "openai/gpt-4o",
    "sonar-pro": "perplexity/sonar-pro",
    "free-gemini": "google/gemini-2.0-flash-exp:free"
}

# Default model preset configuration
DEFAULT_PRESET_MODELS = {
    "1": "google/gemini-2.5-pro-preview-03-25",
    "2": "anthropic/claude-3.7-sonnet",
    "3": "openai/o3-Mini-High",
    "4": "openai/gpt-4.1-mini",
    "5": "perplexity/sonar-pro",
    "6": "google/gemini-2.0-flash-exp:free"  # Will try several free models
}

# Free model fallback list - in order of preference
FREE_MODEL_FALLBACKS = [
    "google/gemini-2.0-flash-exp:free",
    "qwen/qwq-32b:free",
    "deepseek/deepseek-r1-distill-qwen-32b:free",
    "deepseek/deepseek-r1-distill-llama-70b:free",
    "openrouter/optimus-alpha"
]

# Cache for OpenRouter models
OPENROUTER_MODELS_CACHE = {
    "data": None,
    "timestamp": 0,
    "expiry": 3600  # Cache expiry in seconds (1 hour)
}

# Helper function to get the current user identifier
def get_user_identifier():
    if current_user and current_user.is_authenticated:
        return f"user_{current_user.id}"
    
    # If not logged in, use a session-based identifier
    if 'user_identifier' not in session:
        session['user_identifier'] = f"temp_{uuid.uuid4().hex}"
    
    return session['user_identifier']

# Generate a unique, URL-safe share ID for conversations
def generate_share_id(length=12):
    """
    Generate a cryptographically secure random ID for sharing conversations
    
    Args:
        length (int): Length of the resulting ID
        
    Returns:
        str: A URL-safe, base64-encoded random string
    """
    # Generate random bytes and encode to URL-safe base64
    random_bytes = secrets.token_bytes(length)
    share_id = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    
    # Remove any padding characters and trim to desired length
    share_id = share_id.replace('=', '')[:length]
    
    return share_id

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
        
        # Check if this is a direct model ID or one of our shorthand names
        if model_id in OPENROUTER_MODELS:
            # Convert shorthand name to OpenRouter model ID
            openrouter_model = OPENROUTER_MODELS[model_id]
        else:
            # Assume it's already a direct OpenRouter model ID
            openrouter_model = model_id
        
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
            share_id = generate_share_id()
            conversation = Conversation(title=title, share_id=share_id)
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
                                
                                # Create the message with additional metadata fields
                                assistant_db_message = Message(
                                    conversation_id=conversation_id,
                                    role='assistant',
                                    content=full_response,
                                    model=model_id,
                                    model_id_used=None,  # Will be updated if available
                                    prompt_tokens=None,  # Will be updated if available
                                    completion_tokens=None  # Will be updated if available
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
                            
                            # Extract usage information if available (usually in the final chunk)
                            if 'usage' in json_data:
                                usage = json_data['usage']
                                prompt_tokens = usage.get('prompt_tokens')
                                completion_tokens = usage.get('completion_tokens')
                                
                                # Get the exact model ID that was used
                                model_id_used = json_data.get('model', None)
                                
                                # Update the latest assistant message with this information
                                # This assumes the message has already been saved to the database
                                try:
                                    from models import Message
                                    latest_message = Message.query.filter_by(
                                        conversation_id=conversation_id,
                                        role='assistant'
                                    ).order_by(Message.created_at.desc()).first()
                                    
                                    if latest_message:
                                        latest_message.prompt_tokens = prompt_tokens
                                        latest_message.completion_tokens = completion_tokens
                                        latest_message.model_id_used = model_id_used
                                        db.session.commit()
                                        logger.debug(f"Updated message {latest_message.id} with token usage: {prompt_tokens}/{completion_tokens}")
                                except Exception as e:
                                    logger.error(f"Error updating token usage: {e}")
                            
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

@app.route('/models', methods=['GET'])
def get_models():
    """
    Fetch available models from OpenRouter and cache the results
    Adds helper flags for filtering models by type
    """
    try:
        # Check if models are already cached and not expired
        current_time = time.time()
        if (OPENROUTER_MODELS_CACHE["data"] is not None and 
            (current_time - OPENROUTER_MODELS_CACHE["timestamp"]) < OPENROUTER_MODELS_CACHE["expiry"]):
            return Response(json.dumps(OPENROUTER_MODELS_CACHE["data"]), content_type='application/json')
        
        # Get API key from environment
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            logger.error("OPENROUTER_API_KEY not found in environment variables")
            return Response(json.dumps({"error": "API key not configured"}), 
                           content_type='application/json', status=500)
        
        # Prepare headers for OpenRouter API
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Fetch models from OpenRouter
        response = requests.get(
            'https://openrouter.ai/api/v1/models',
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            return Response(json.dumps({"error": f"API Error: {response.status_code}"}), 
                           content_type='application/json', status=500)
        
        # Parse the response
        models_data = response.json()
        
        # Process models to add custom flags for filtering
        for model in models_data.get('data', []):
            model_id = model.get('id', '').lower()
            model_name = model.get('name', '').lower()
            model_description = model.get('description', '').lower()
            
            # Set flags based on model properties
            model['is_free'] = ':free' in model_id or model.get('pricing', {}).get('prompt') == 0
            model['is_multimodal'] = any(keyword in model_id or keyword in model_name or keyword in model_description 
                                        for keyword in ['vision', 'image', 'multi', 'gpt-4o'])
            model['is_perplexity'] = 'perplexity' in model_id or 'perplexity' in model_name
            model['is_reasoning'] = any(keyword in model_id or keyword in model_name or keyword in model_description 
                                      for keyword in ['reasoning', 'large', 'opus', 'small'])
        
        # Update cache
        OPENROUTER_MODELS_CACHE["data"] = models_data
        OPENROUTER_MODELS_CACHE["timestamp"] = current_time
        
        return Response(json.dumps(models_data), content_type='application/json')
    
    except Exception as e:
        logger.exception("Error fetching models")
        return Response(json.dumps({"error": str(e)}), content_type='application/json', status=500)

@app.route('/save_preference', methods=['POST'])
def save_preference():
    """
    Save user model preference for a specific preset button
    """
    try:
        data = request.get_json()
        preset_id = data.get('preset_id')
        model_id = data.get('model_id')
        
        # Validate input
        if not preset_id or not model_id:
            return Response(json.dumps({"error": "Missing preset_id or model_id"}), 
                           content_type='application/json', status=400)
        
        try:
            preset_id = int(preset_id)
            if preset_id < 1 or preset_id > 6:
                return Response(json.dumps({"error": "preset_id must be between 1 and 6"}), 
                               content_type='application/json', status=400)
        except ValueError:
            return Response(json.dumps({"error": "preset_id must be a number"}), 
                           content_type='application/json', status=400)
        
        # Get user identifier
        user_identifier = get_user_identifier()
        
        # Import UserPreference model
        from models import UserPreference
        
        # Check if preference already exists
        preference = UserPreference.query.filter_by(
            user_identifier=user_identifier,
            preset_id=preset_id
        ).first()
        
        if preference:
            # Update existing preference
            preference.model_id = model_id
        else:
            # Create new preference
            preference = UserPreference(
                user_identifier=user_identifier,
                preset_id=preset_id,
                model_id=model_id,
                user_id=current_user.id if current_user and current_user.is_authenticated else None
            )
            db.session.add(preference)
        
        db.session.commit()
        
        return Response(json.dumps({"success": True, "message": "Preference saved successfully"}), 
                       content_type='application/json')
    
    except Exception as e:
        logger.exception("Error saving preference")
        db.session.rollback()
        return Response(json.dumps({"error": str(e)}), content_type='application/json', status=500)

@app.route('/get_preferences', methods=['GET'])
def get_preferences():
    """
    Get all user preferences for model presets
    """
    try:
        # Get user identifier
        user_identifier = get_user_identifier()
        
        # Import UserPreference model
        from models import UserPreference
        
        # Query for preferences
        preferences = UserPreference.query.filter_by(user_identifier=user_identifier).all()
        
        # Build response with preferences
        result = {}
        for preference in preferences:
            result[str(preference.preset_id)] = preference.model_id
        
        # Add default models for presets not yet configured
        for preset_id in map(str, range(1, 7)):
            if preset_id not in result:
                result[preset_id] = DEFAULT_PRESET_MODELS[preset_id]
        
        return Response(json.dumps({"preferences": result}), content_type='application/json')
    
    except Exception as e:
        logger.exception("Error getting preferences")
        return Response(json.dumps({"error": str(e)}), content_type='application/json', status=500)

@app.route('/rate_message/<int:message_id>', methods=['POST'])
def rate_message(message_id):
    """
    Rate a message with an upvote or downvote
    
    Accepts a POST request with JSON body: {'rating': 1} or {'rating': -1}
    """
    try:
        data = request.get_json()
        rating = data.get('rating')
        
        # Validate input
        if rating is None or rating not in [1, -1, 0]:
            return Response(json.dumps({"error": "Rating must be 1, -1, or 0"}), 
                          content_type='application/json', status=400)
        
        # Import Message model
        from models import Message
        
        # Get the message
        message = Message.query.get(message_id)
        if not message:
            return Response(json.dumps({"error": "Message not found"}), 
                          content_type='application/json', status=404)
        
        # Update the rating
        message.rating = rating
        db.session.commit()
        
        return Response(json.dumps({"success": True, "message": "Rating saved"}), 
                       content_type='application/json')
    
    except Exception as e:
        logger.exception("Error saving rating")
        db.session.rollback()
        return Response(json.dumps({"error": str(e)}), content_type='application/json', status=500)

@app.route('/conversation/<int:conversation_id>/share', methods=['POST'])
def share_conversation(conversation_id):
    """
    Generate or retrieve a share link for a conversation
    
    Returns a JSON object with the share URL
    """
    try:
        # Import the model
        from models import Conversation
        
        # Get the conversation
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            return Response(json.dumps({"error": "Conversation not found"}), 
                          content_type='application/json', status=404)
        
        # If the conversation doesn't have a share_id yet, generate one
        if not conversation.share_id:
            conversation.share_id = generate_share_id()
            db.session.commit()
        
        # Return the share URL
        share_url = f'/share/{conversation.share_id}'
        return Response(json.dumps({"share_url": share_url}), content_type='application/json')
    
    except Exception as e:
        logger.exception("Error sharing conversation")
        db.session.rollback()
        return Response(json.dumps({"error": str(e)}), content_type='application/json', status=500)

@app.route('/share/<share_id>')
def view_shared_conversation(share_id):
    """
    Display a shared conversation
    
    This endpoint renders the same chat template but with a readonly flag
    """
    try:
        # Import the model
        from models import Conversation
        
        # Find the conversation by share_id
        conversation = Conversation.query.filter_by(share_id=share_id).first()
        if not conversation:
            flash("The shared conversation link is invalid or has expired.")
            return redirect(url_for('index'))
        
        # In a real implementation, you would load the messages and render them
        # For now, just redirect to the home page
        return redirect(url_for('index'))
    
    except Exception as e:
        logger.exception("Error viewing shared conversation")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
