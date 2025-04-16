# --- Complete app.py (Synchronous Version - Reverted & Fixed) ---
import os
import logging
import json
import requests # Use requests for synchronous calls
# import httpx # No longer needed
import uuid
import time
import base64
import secrets
from flask import Flask, render_template, request, Response, session, jsonify, abort, url_for, redirect, flash, stream_with_context # Added stream_with_context back
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
else:
    # Define dummy functions if memory system is disabled to avoid errors later
    def save_message_with_memory(*args, **kwargs):
        pass # No-op
    def enrich_prompt_with_memory(session_id, user_id, user_message, conversation_history):
        return conversation_history # Return original history


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
if not app.secret_key:
     logger.warning("SESSION_SECRET environment variable not set. Using default for development.")
     app.secret_key = "default-dev-secret-key-please-change"


# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
if not app.config["SQLALCHEMY_DATABASE_URI"]:
    logger.error("DATABASE_URL environment variable not set.")
    # Handle this critical error appropriately

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
login_manager.login_view = 'login' # Replace 'login' with your actual login route if different

@login_manager.user_loader
def load_user(user_id):
    from models import User 
    try:
        # Use db.session.get() for primary key lookup if using SQLAlchemy 2.0+ style
        return db.session.get(User, int(user_id))
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {e}")
        return None

# --- Model Mappings & Defaults ---
OPENROUTER_MODELS = {
    "gemini-1.5-pro": "google/gemini-2.5-pro-preview-03-25",
    "claude-3-sonnet": "anthropic/claude-3.7-sonnet",
    "mistral-large": "mistralai/mistral-large",
    "gpt-4o": "openai/gpt-4o",
    "sonar-pro": "perplexity/sonar-pro",
    "free-gemini": "google/gemini-2.0-flash-exp:free"
}
DEFAULT_PRESET_MODELS = {
    "1": "google/gemini-2.5-pro-preview-03-25",
    "2": "anthropic/claude-3.7-sonnet",
    "3": "openai/o3-Mini-High",
    "4": "openai/gpt-4.1-mini",
    "5": "perplexity/sonar-pro",
    "6": "google/gemini-2.0-flash-exp:free"
}
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

# --- Helper Functions ---
def get_user_identifier():
    if current_user and current_user.is_authenticated:
        return f"user_{current_user.id}"

    if 'user_identifier' not in session:
        session['user_identifier'] = f"temp_{uuid.uuid4().hex}"
        logger.debug(f"Generated new temporary user ID: {session['user_identifier']}")

    return session['user_identifier']

def generate_share_id(length=12):
    random_bytes = secrets.token_bytes(length)
    share_id = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    share_id = share_id.replace('=', '')[:length]
    return share_id

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/conversations', methods=['GET'])
def get_conversations():
    # Basic placeholder - Needs proper implementation
    try:
        from models import Conversation
        existing_convo = Conversation.query.first() 
        if not existing_convo:
             title = "Demo Conversation"
             share_id = generate_share_id()
             conversation = Conversation(title=title, share_id=share_id)
             db.session.add(conversation)
             try:
                 db.session.commit()
                 logger.info("Created initial Demo Conversation")
                 conversations = [{"id": conversation.id, "title": conversation.title}]
             except Exception as e:
                  logger.exception("Error committing demo conversation")
                  db.session.rollback()
                  conversations = []
        else:
             # Replace with actual user-specific query later
             conversations = [{"id": existing_convo.id, "title": existing_convo.title}]

        return jsonify({"conversations": conversations})
    except Exception as e:
        logger.exception("Error getting conversations")
        return jsonify({"error": str(e)}), 500

# --- SYNCHRONOUS CHAT ENDPOINT (Using Requests) ---
@app.route('/chat', methods=['POST'])
def chat(): # Synchronous function
    """
    Endpoint to handle chat messages and stream responses from OpenRouter (SYNC Version)
    """
    try:
        # --- Get request data ---
        data = request.get_json()
        if not data:
            logger.error("Request body is not JSON or is empty")
            abort(400, description="Invalid request body. JSON expected.")

        user_message = data.get('message', '')
        # Use .get for default model to avoid KeyError if '1' isn't present initially
        model_id = data.get('model', DEFAULT_PRESET_MODELS.get('1', 'google/gemini-flash-1.5')) 
        message_history = data.get('history', [])
        conversation_id = data.get('conversation_id', None)

        from models import Conversation, Message # Ensure models are imported

        # --- Determine OpenRouter Model ID ---
        openrouter_model = OPENROUTER_MODELS.get(model_id, model_id) # Use .get fallback

        # --- Get API Key ---
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            logger.error("OPENROUTER_API_KEY not found")
            abort(500, description="API key not configured")

        # --- Prepare Headers ---
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': request.headers.get('Referer', 'http://localhost:5000') # Adjust if needed
        }

        # --- Get/Create Conversation & Save User Message ---
        # (Using the logic refined during async attempts)
        conversation = None
        if conversation_id:
            conversation = db.session.get(Conversation, conversation_id) 
            if not conversation:
                 logger.warning(f"Conversation ID {conversation_id} not found, creating new.")
                 conversation_id = None 

        if not conversation_id: 
            title = user_message[:50] + "..." if len(user_message) > 50 else user_message
            if not title: title = "New Conversation"
            share_id = generate_share_id() 
            conversation = Conversation(title=title, share_id=share_id)
            # if current_user and current_user.is_authenticated: # Add user linking if needed
            #    conversation.user_id = current_user.id
            db.session.add(conversation)
            try:
                db.session.commit()
                conversation_id = conversation.id 
                logger.info(f"Created new conversation with ID: {conversation_id}")
            except Exception as e:
                 logger.exception("Error committing new conversation")
                 db.session.rollback()
                 abort(500, description="Database error creating conversation")

        if not conversation or not conversation.id:
             logger.error("Failed to get or create a valid conversation object.")
             abort(500, description="Failed to establish conversation context.")

        user_db_message = Message(
            conversation_id=conversation.id, role='user', content=user_message
        )
        db.session.add(user_db_message)
        try:
             db.session.commit()
             logger.info(f"Saved user message {user_db_message.id} for conversation {conversation.id}")
        except Exception as e:
             logger.exception(f"Error committing user message {user_db_message.id}")
             db.session.rollback()
             abort(500, description="Database error saving user message")


        # --- Prepare Message History ---
        system_message = ( # Make sure this is defined correctly
             "You are a helpful assistant at GloriaMundo, an advanced AI chat platform. "
             "Provide detailed, accurate, and helpful responses to user queries. "
             "Write in a conversational yet professional tone. "
             "If you don't know something, say so rather than making up information. "
             "Format responses with clear structure using paragraphs, lists, and emphasis when appropriate."
         )
        messages = [{'role': 'system', 'content': system_message}]

        db_messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
        for msg in db_messages:
             if msg.id != user_db_message.id: 
                 messages.append({'role': msg.role, 'content': msg.content})

        messages.append({'role': 'user', 'content': user_message}) 

        # --- Enrich with memory if needed ---
        if ENABLE_MEMORY_SYSTEM:
            try:
                memory_user_id = str(current_user.id) if current_user and current_user.is_authenticated else f"anonymous_{conversation.id}"
                enriched_messages = enrich_prompt_with_memory(
                     session_id=str(conversation.id), user_id=memory_user_id, 
                     user_message=user_message, conversation_history=messages
                )
                if len(enriched_messages) > len(messages):
                     logger.info(f"Added {len(enriched_messages) - len(messages)} context messages from memory system")
                messages = enriched_messages
            except Exception as e:
                 logger.error(f"Error enriching with memory: {e}")

        # --- Prepare Payload ---
        payload = {
            'model': openrouter_model,
            'messages': messages,
            'stream': True,
            'reasoning': {}  # Enable reasoning tokens for all models that support it
        }
        logger.debug(f"Sending request to OpenRouter with model: {openrouter_model}. History length: {len(messages)}, reasoning enabled")

        # --- Define the SYNC Generator using requests ---
        def generate():
            assistant_response_content = [] 
            final_prompt_tokens = None
            final_completion_tokens = None
            final_model_id_used = None
            assistant_message_id = None 
            current_conv_id = conversation.id 
            requested_model_id = model_id 

            try:
                # Use standard requests.post with stream=True
                response = requests.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers, 
                    json=payload,    
                    stream=True,
                    # Consider a timeout for the entire request duration if needed
                    timeout=300.0 
                )

                # Check status *after* making the request
                if response.status_code != 200:
                    error_text = response.text 
                    logger.error(f"OpenRouter API error: {response.status_code} - {error_text}")
                    yield f"data: {json.dumps({'type': 'error', 'error': f'API Error: {response.status_code} - {error_text}'})}\n\n"
                    return # Stop generation

                # Iterate over the stream using iter_lines
                for line in response.iter_lines():
                    if line:
                        if line.strip() == b'': continue 

                        line_text = line.decode('utf-8')

                        if line_text.startswith('data: '):
                            # Get raw data without the 'data: ' prefix
                            raw_data = line_text[6:].strip()
                            # Get bytes data for byte-level comparisons
                            sse_data = line[6:].strip()

                            # *** ENHANCED FIX: More thorough check for [DONE] marker ***
                            # Check both string and bytes versions for more robustness
                            if raw_data == '[DONE]' or sse_data == b'[DONE]':
                                logger.debug("Received [DONE] marker. Skipping without JSON parsing.")
                                continue # Go to next line, post-loop logic handles completion
                            elif not raw_data:
                                logger.debug("Empty SSE data, skipping.")
                                continue # Skip empty data
                            else:
                                # --- If it's not [DONE], *then* try to parse JSON ---
                                try: 
                                    # Decode the raw bytes to string for JSON parsing if needed
                                    data_to_parse = raw_data if isinstance(raw_data, str) else raw_data.decode('utf-8')
                                    if not data_to_parse: 
                                        continue # Skip if data part is empty after stripping
                                    
                                    # Check again for [DONE] string just to be sure
                                    if data_to_parse == '[DONE]':
                                        logger.debug("Detected [DONE] during JSON parsing. Skipping.")
                                        continue
                                        
                                    json_data = json.loads(data_to_parse)
                                    logger.debug(f"JSON parsed successfully: type '{json_data.get('type', 'N/A')}'")

                                    # --- Extract Content and Reasoning ---
                                    content_chunk = None
                                    reasoning_chunk = None
                                    
                                    if 'choices' in json_data and len(json_data['choices']) > 0:
                                        choice = json_data['choices'][0]
                                        delta = choice.get('delta', {})
                                        
                                        # Extract content if available
                                        if delta.get('content') is not None:
                                            content_chunk = delta['content']
                                            
                                        # Extract reasoning if available
                                        if delta.get('reasoning') is not None:
                                            reasoning_chunk = delta['reasoning']
                                            logger.debug(f"Received reasoning chunk: {reasoning_chunk[:50]}...")

                                    # Handle content chunk
                                    if content_chunk:
                                        assistant_response_content.append(content_chunk)
                                        # Yield content chunk to the client
                                        yield f"data: {json.dumps({'type': 'content', 'content': content_chunk, 'conversation_id': current_conv_id})}\n\n"
                                    
                                    # Handle reasoning chunk
                                    if reasoning_chunk:
                                        # Yield reasoning chunk to the client
                                        yield f"data: {json.dumps({'type': 'reasoning', 'reasoning': reasoning_chunk, 'conversation_id': current_conv_id})}\n\n"

                                    # --- Extract Usage/Model ---
                                    if 'usage' in json_data and json_data['usage']: 
                                        usage = json_data['usage']
                                        final_prompt_tokens = usage.get('prompt_tokens')
                                        final_completion_tokens = usage.get('completion_tokens')
                                        logger.debug(f"Extracted usage data: P:{final_prompt_tokens} C:{final_completion_tokens}")

                                    if 'model' in json_data and json_data['model']:
                                        final_model_id_used = json_data.get('model')
                                        logger.debug(f"Extracted model used: {final_model_id_used}")

                                except json.JSONDecodeError as e:
                                    # This should only catch legitimate JSON parsing errors, not [DONE] markers
                                    data_info = f"'{data_to_parse}'" if len(str(data_to_parse)) < 100 else f"'{data_to_parse[:100]}...' (truncated)"
                                    logger.error(f"JSON decode error: {e} on input data: {data_info}")
                                    
                                    # If we suspect this is a [DONE] marker that wasn't caught earlier, just skip it
                                    if '[DONE]' in str(data_to_parse):
                                        logger.warning("Detected possible [DONE] in error data - skipping without error")
                                        continue
                                    
                                    # Otherwise, treat it as a real error
                                    yield f"data: {json.dumps({'type': 'error', 'error': 'JSON parsing error'})}\n\n"
                                    return # Stop generation on genuine parsing error

                # --- Stream processing finished ---
                full_response_text = ''.join(assistant_response_content)

                if full_response_text: # Only save if there was actual content
                    try:
                        from models import Message 
                        assistant_db_message = Message(
                            conversation_id=current_conv_id, 
                            role='assistant', 
                            content=full_response_text,
                            model=requested_model_id, 
                            model_id_used=final_model_id_used, 
                            prompt_tokens=final_prompt_tokens, 
                            completion_tokens=final_completion_tokens,
                            rating=None 
                        )
                        db.session.add(assistant_db_message)
                        db.session.commit()
                        assistant_message_id = assistant_db_message.id 
                        logger.info(f"Saved assistant message {assistant_message_id} with metadata.")

                        # Save to memory system if enabled
                        if ENABLE_MEMORY_SYSTEM:
                             try:
                                 memory_user_id = str(current_user.id) if current_user and current_user.is_authenticated else f"anonymous_{current_conv_id}"
                                 save_message_with_memory(
                                     session_id=str(current_conv_id), user_id=memory_user_id, 
                                     role='assistant', content=full_response_text
                                 )
                             except Exception as e:
                                 logger.error(f"Error saving assistant message to memory: {e}")

                        # Yield the final metadata event
                        logger.info(f"==> Preparing to yield METADATA for message {assistant_message_id}")
                        yield f"data: {json.dumps({'type': 'metadata', 'metadata': {'id': assistant_message_id, 'model_id_used': final_model_id_used, 'prompt_tokens': final_prompt_tokens, 'completion_tokens': final_completion_tokens}})}\n\n"
                        logger.info(f"==> SUCCESSFULLY yielded METADATA for message {assistant_message_id}")

                    except Exception as db_error:
                        logger.exception("Error saving assistant message or metadata to DB")
                        db.session.rollback()
                        yield f"data: {json.dumps({'type': 'error', 'error': 'Error saving message to database'})}\n\n"
                else:
                     logger.info("Assistant response was empty, not saving to DB or yielding metadata.")

                # Signal completion to the client
                logger.info("==> Preparing to yield DONE event")
                # Add an additional newline at the end to properly terminate the SSE stream
                yield f"data: {json.dumps({'type': 'done', 'done': True, 'conversation_id': current_conv_id})}\n\n\n"
                logger.info("==> SUCCESSFULLY yielded DONE event. Stream generation complete.")

            except requests.exceptions.RequestException as e: # Catch requests errors
                 logger.exception(f"Requests error during stream: {e}")
                 yield f"data: {json.dumps({'type': 'error', 'error': f'Connection error: {e}'})}\n\n"
            except Exception as e:
                # Catch any other unexpected errors during generation
                logger.exception("Error during sync stream generation processing")
                yield f"data: {json.dumps({'type': 'error', 'error': f'Stream Processing Error: {str(e)}'})}\n\n"

        # --- Return the Response object wrapping the sync generator with context ---
        # Use stream_with_context for sync generators in Flask
        return Response(stream_with_context(generate()), content_type='text/event-stream') 

    except Exception as e:
        # Catch errors during initial setup before generation starts
        logger.exception("Error in chat endpoint setup")
        abort(500, description=f"Chat endpoint setup error: {str(e)}") 
# === END OF SYNC chat() ENDPOINT ===


# --- Other Synchronous Routes (Keep As Is) ---
@app.route('/models', methods=['GET'])
def get_models():
    """ Fetch available models """
    try:
        current_time = time.time()
        if (OPENROUTER_MODELS_CACHE["data"] is not None and 
            (current_time - OPENROUTER_MODELS_CACHE["timestamp"]) < OPENROUTER_MODELS_CACHE["expiry"]):
            logger.debug("Returning cached models")
            return jsonify(OPENROUTER_MODELS_CACHE["data"])

        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            logger.error("OPENROUTER_API_KEY not found")
            abort(500, description="API key not configured")

        headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}

        logger.debug("Fetching models from OpenRouter...")
        response = requests.get( # Make sure requests is imported
            'https://openrouter.ai/api/v1/models',
            headers=headers,
            timeout=15.0 
        )

        response.raise_for_status() 
        models_data = response.json()

        processed_models = []
        for model in models_data.get('data', []):
            model_id = model.get('id', '').lower()
            model_name = model.get('name', '').lower()
            model_description = model.get('description', '').lower()

            try:
                prompt_price = float(model.get('pricing', {}).get('prompt', '1.0'))
            except (ValueError, TypeError):
                prompt_price = 1.0 

            model['is_free'] = ':free' in model_id or prompt_price == 0.0
            model['is_multimodal'] = any(keyword in model_id or keyword in model_name or keyword in model_description 
                                           for keyword in ['vision', 'image', 'multi', 'gpt-4o'])
            model['is_perplexity'] = 'perplexity/' in model_id
            model['is_reasoning'] = any(keyword in model_id or keyword in model_name or keyword in model_description 
                                           for keyword in ['reasoning', 'opus', 'o1', 'o3']) 
            processed_models.append(model)

        result_data = {"data": processed_models} 

        OPENROUTER_MODELS_CACHE["data"] = result_data
        OPENROUTER_MODELS_CACHE["timestamp"] = current_time
        logger.info(f"Fetched and cached {len(processed_models)} models from OpenRouter")

        return jsonify(result_data)

    except requests.exceptions.RequestException as e:
        logger.exception("Error fetching models from OpenRouter API")
        abort(500, description=f"API Error fetching models: {e}")
    except Exception as e:
        logger.exception("Error processing models data")
        abort(500, description=f"Server error processing models: {e}")


@app.route('/save_preference', methods=['POST'])
def save_preference():
    """ Save user model preference """
    try:
        data = request.get_json()
        if not data: abort(400, description="Invalid request body. JSON expected.")
        preset_id = data.get('preset_id')
        model_id = data.get('model_id')
        if not preset_id or not model_id: abort(400, description="Missing preset_id or model_id")
        try:
            preset_id = int(preset_id)
            if not 1 <= preset_id <= 6: abort(400, description="preset_id must be between 1 and 6")
        except ValueError: abort(400, description="preset_id must be a number")

        user_identifier = get_user_identifier()
        from models import UserPreference 

        preference = UserPreference.query.filter_by(user_identifier=user_identifier, preset_id=preset_id).first()

        if preference:
            preference.model_id = model_id
        else:
            preference = UserPreference(
                user_identifier=user_identifier, preset_id=preset_id, model_id=model_id,
                user_id=current_user.id if current_user and current_user.is_authenticated else None )
            db.session.add(preference)

        db.session.commit()
        return jsonify({"success": True, "message": "Preference saved successfully"})
    except Exception as e:
        logger.exception("Error saving preference")
        db.session.rollback()
        abort(500, description=str(e))


@app.route('/get_preferences', methods=['GET'])
def get_preferences():
    """ Get all user preferences """
    try:
        user_identifier = get_user_identifier()
        from models import UserPreference 

        preferences = UserPreference.query.filter_by(user_identifier=user_identifier).all()
        result = {str(p.preset_id): p.model_id for p in preferences}

        for preset_id_str, default_model in DEFAULT_PRESET_MODELS.items():
            if preset_id_str not in result:
                result[preset_id_str] = default_model

        return jsonify({"preferences": result})
    except Exception as e:
        logger.exception("Error getting preferences")
        abort(500, description=str(e))


@app.route('/message/<int:message_id>/rate', methods=['POST']) 
def rate_message(message_id):
    """ Rate a message """
    try:
        data = request.get_json()
        if not data: abort(400, description="Invalid request body. JSON expected.")
        rating = data.get('rating')
        if rating is None or rating not in [1, -1, 0]: abort(400, description="Rating must be 1, -1, or 0")

        from models import Message 
        message = db.session.get(Message, message_id) 
        if not message: abort(404, description="Message not found")

        message.rating = rating if rating in [1, -1] else None 
        db.session.commit()
        logger.info(f"Saved rating {rating} for message {message_id}")
        return jsonify({"success": True, "message": "Rating saved"})
    except Exception as e:
        logger.exception(f"Error saving rating for message {message_id}")
        db.session.rollback()
        abort(500, description=str(e))


@app.route('/conversation/<int:conversation_id>/share', methods=['POST']) 
def share_conversation(conversation_id):
    """ Generate or retrieve share link """
    try:
        from models import Conversation 
        conversation = db.session.get(Conversation, conversation_id) 
        if not conversation: abort(404, description="Conversation not found")

        if not conversation.share_id:
            conversation.share_id = generate_share_id()
            db.session.commit()
            logger.info(f"Generated share ID for conversation {conversation_id}")

        share_url_path = url_for('view_shared_conversation', share_id=conversation.share_id, _external=False) # Ensure relative path
        return jsonify({"share_url": share_url_path})
    except Exception as e:
        logger.exception(f"Error sharing conversation {conversation_id}")
        db.session.rollback()
        abort(500, description=str(e))


@app.route('/conversation/<int:conversation_id>/summarize', methods=['POST'])
def summarize_conversation(conversation_id):
    """ Generate a title summary for a conversation """
    try:
        # Import models
        from models import Conversation, Message, UserPreference
        
        # Get the conversation
        conversation = db.session.get(Conversation, conversation_id)
        if not conversation: 
            abort(404, description="Conversation not found")
        
        # Get the first user message and first assistant message
        first_user_message = conversation.messages.filter_by(role='user').order_by(Message.created_at).first()
        first_assistant_message = conversation.messages.filter_by(role='assistant').order_by(Message.created_at).first()
        
        if not first_user_message or not first_assistant_message:
            return jsonify({"title": "New Conversation", "error": "Incomplete conversation"})
        
        # Get the model ID for Preset 6 (free model)
        user_identifier = get_user_identifier()
        preset_6_preference = UserPreference.query.filter_by(
            user_identifier=user_identifier, 
            preset_id=6
        ).first()
        
        if preset_6_preference:
            model_id = preset_6_preference.model_id
        else:
            # Default free model
            model_id = "meta-llama/llama-3.2-3b-instruct:free"
        
        # Construct the prompt
        prompt = f"""Generate a concise title (max 5 words) for this conversation start:

User: {first_user_message.content}
Assistant: {first_assistant_message.content}

Title:"""
        
        # Get API Key
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            logger.error("OPENROUTER_API_KEY not found")
            abort(500, description="API key not configured")
        
        # Prepare headers
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Prepare payload
        payload = {
            'model': model_id,
            'messages': [{"role": "user", "content": prompt}],
            'max_tokens': 15,  # Short response
            'temperature': 0.7
        }
        
        # Make non-streaming request to OpenRouter
        logger.debug(f"Sending summarization request to OpenRouter with model: {model_id}")
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=15.0  # Short timeout for title generation
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extract the title from the response
        generated_title = result['choices'][0]['message']['content'].strip()
        
        # Clean up the title (remove quotes or any other unwanted characters)
        generated_title = generated_title.strip('"\'').strip()
        
        # Truncate if too long (max 100 chars as per DB column)
        if len(generated_title) > 100:
            generated_title = generated_title[:97] + "..."
        
        # Update the conversation title
        conversation.title = generated_title
        db.session.commit()
        
        logger.info(f"Generated title for conversation {conversation_id}: {generated_title}")
        return jsonify({"title": generated_title})
        
    except Exception as e:
        logger.exception(f"Error summarizing conversation {conversation_id}")
        db.session.rollback()
        
        # Return a generic title in case of error
        return jsonify({"title": "New Conversation", "error": str(e)})


@app.route('/share/<share_id>')
def view_shared_conversation(share_id):
    """ Display shared conversation (Placeholder) """
    try:
        from models import Conversation 
        conversation = Conversation.query.filter_by(share_id=share_id).first()
        if not conversation:
            flash("The shared conversation link is invalid or has expired.", "warning")
            return redirect(url_for('index'))

        logger.info(f"Viewing shared conversation placeholder for ID: {share_id}")
        flash(f"Shared conversation view not yet implemented (ID: {share_id}).", "info")
        return redirect(url_for('index'))

    except Exception as e:
        logger.exception(f"Error viewing shared conversation {share_id}")
        flash("An error occurred while trying to load the shared conversation.", "error")
        return redirect(url_for('index'))

# --- Main Execution ---
if __name__ == '__main__':
    logger.info("Starting Flask development server")
    # Use debug=False if running with Gunicorn/Uvicorn in production
    # The threaded=True option might offer slightly better handling of concurrent requests
    # for the dev server compared to the default, but Gunicorn handles concurrency differently.
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)