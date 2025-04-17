# --- Complete app.py (Synchronous Version - Reverted & Fixed) ---
# IMPORTANT: Monkey patching must happen at the very top, before any other imports
from gevent import monkey
monkey.patch_all()

import os
import io
import logging
# Configure pymongo logging to reduce noise
logging.getLogger('pymongo').setLevel(logging.WARNING)
import json
import requests # Use requests for synchronous calls
# import httpx # No longer needed
import uuid
import time
import base64
import secrets
import threading
from flask import Flask, render_template, request, Response, session, jsonify, abort, url_for, redirect, flash, stream_with_context # Added stream_with_context back
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, current_user, login_required

# Check if we should enable advanced memory features
ENABLE_MEMORY_SYSTEM = os.environ.get('ENABLE_MEMORY_SYSTEM', 'false').lower() == 'true'

# Check if we should enable RAG features
ENABLE_RAG = os.environ.get('ENABLE_RAG', 'true').lower() == 'true'

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
        
# Initialize document processor for RAG if enabled
if ENABLE_RAG:
    try:
        from document_processor import DocumentProcessor
        document_processor = DocumentProcessor()
        logging.info("RAG functionality enabled")
    except ImportError as e:
        logging.warning(f"Failed to import document processor: {e}")
        ENABLE_RAG = False


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

def generate_summary(conversation_id):
    """
    Generate a short, descriptive title for a conversation using OpenRouter LLM.
    This function runs non-blocking under gevent to avoid blocking the server.
    
    Args:
        conversation_id: The ID of the conversation to summarize
    """
    print(f"[SUMMARIZE {conversation_id}] Function called.") # ADDED
    try:
        logger.info(f"Generating summary for conversation {conversation_id}")
        from models import Conversation, Message
        
        # Check if title is already customized (not the default)
        conversation = db.session.get(Conversation, conversation_id)
        if not conversation:
            print(f"[SUMMARIZE {conversation_id}] Conversation not found in database.") # ADDED
            logger.warning(f"Conversation {conversation_id} not found when generating summary")
            return
            
        if conversation.title != "New Conversation":
            print(f"[SUMMARIZE {conversation_id}] Already has title: {conversation.title}") # ADDED
            logger.info(f"Conversation {conversation_id} already has a custom title: '{conversation.title}'. Skipping.")
            return
        else:
            print(f"[SUMMARIZE {conversation_id}] No existing summary found, proceeding.") # ADDED
            
        # Get all messages, ordered by creation time
        messages = Message.query.filter_by(conversation_id=conversation_id)\
            .order_by(Message.created_at)\
            .all()
            
        if len(messages) < 2:
            print(f"[SUMMARIZE {conversation_id}] Not enough messages ({len(messages)}) to summarize.") # ADDED
            logger.warning(f"Not enough messages in conversation {conversation_id} to generate summary")
            return
        else:
            print(f"[SUMMARIZE {conversation_id}] Found {len(messages)} total messages.") # ADDED
            
        # Find the first user message and its corresponding assistant response
        user_message = None
        assistant_message = None
        
        for i, message in enumerate(messages):
            if message.role == 'user':
                # Try to find the assistant message that follows this user message
                if i + 1 < len(messages) and messages[i + 1].role == 'assistant':
                    user_message = message.content
                    assistant_message = messages[i + 1].content
                    print(f"[SUMMARIZE {conversation_id}] Found user-assistant pair at positions {i} and {i+1}") # ADDED
                    break  # Found a user-assistant pair, we can stop searching
        
        if not user_message or not assistant_message:
            print(f"[SUMMARIZE {conversation_id}] Missing user or assistant message.") # ADDED
            logger.warning(f"Missing user or assistant message in conversation {conversation_id}")
            return
            
        # Get API Key
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            print(f"[SUMMARIZE {conversation_id}] OPENROUTER_API_KEY not found.") # ADDED
            logger.error("OPENROUTER_API_KEY not found while generating summary")
            return
            
        # Use the free model for summarization
        model_id = DEFAULT_PRESET_MODELS.get('6', 'google/gemini-2.0-flash-exp:free')
        
        # Prepare the prompt for summarization
        summary_prompt = [
            {
                "role": "system", 
                "content": "You are a specialized AI that creates concise, descriptive conversation titles. Create extremely short titles (3-5 words maximum) that accurately capture the conversation's main topic. Always respond with ONLY the title text - no quotes, explanations, or additional text."
            },
            {
                "role": "user", 
                "content": f"Generate a concise, descriptive title (3-5 words maximum) for this conversation:\n\nUser: {user_message}\n\nAssistant: {assistant_message[:300]}...\n\nTitle:"
            }
        ]
        
        # Prepare headers
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'http://localhost:5000'  # Adjust if needed
        }
        
        # Prepare payload - use a lower max_tokens since we only need a short title
        payload = {
            'model': model_id,
            'messages': summary_prompt,
            'max_tokens': 20,  # Limit token count since we only need a short title
            'temperature': 0.7  # Slightly creative but not too random
        }
        
        # Make the API request
        print(f"[SUMMARIZE {conversation_id}] Prompt constructed. About to call API with model {model_id}.") # ADDED
        print(f"[SUMMARIZE {conversation_id}] API Key: {'VALID' if api_key else 'MISSING'}")
        print(f"[SUMMARIZE {conversation_id}] Headers: {headers}")
        print(f"[SUMMARIZE {conversation_id}] Payload: {payload}")
        logger.info(f"Sending title generation request to OpenRouter with model: {model_id}")
        
        try:
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=20.0  # Increased timeout for more reliability
            )
        except requests.exceptions.Timeout:
            print(f"[SUMMARIZE {conversation_id}] API request timed out after 20 seconds")
            logger.error(f"OpenRouter API timeout during title generation for conversation {conversation_id}")
            return
        except requests.exceptions.RequestException as e:
            print(f"[SUMMARIZE {conversation_id}] API request error: {e}")
            logger.error(f"OpenRouter API error during title generation: {e}")
            return
        
        print(f"[SUMMARIZE {conversation_id}] API call finished. Status: {response.status_code}") # ADDED
        
        if response.status_code != 200:
            print(f"[SUMMARIZE {conversation_id}] API error: {response.status_code} - {response.text[:100]}") # ADDED
            logger.error(f"OpenRouter API error while generating title: {response.status_code} - {response.text}")
            return
            
        # Process the response
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            title_text = response_data['choices'][0]['message']['content'].strip()
            print(f"[SUMMARIZE {conversation_id}] Summary extracted: {title_text}") # ADDED
            
            # Clean up the title (remove quotes, etc.)
            title_text = title_text.strip('"\'')
            if len(title_text) > 50:
                title_text = title_text[:47] + "..."
                
            # Update the conversation title and updated_at timestamp
            from datetime import datetime 
            conversation.title = title_text
            conversation.updated_at = datetime.utcnow()  # Explicitly update the timestamp
            print(f"[SUMMARIZE {conversation_id}] Updating DB title with fresh timestamp") # ADDED
            db.session.commit()
            print(f"[SUMMARIZE {conversation_id}] DB commit successful.") # ADDED
            logger.info(f"Updated conversation {conversation_id} title to: '{title_text}' with new timestamp")
        else:
            print(f"[SUMMARIZE {conversation_id}] Failed to extract title from API response: {response_data}") # ADDED
            logger.warning(f"Failed to extract title from API response: {response_data}")
            
    except Exception as e:
        # Use traceback for more detailed error information
        import traceback
        print(f"[SUMMARIZE {conversation_id}] Error during summarization:") # ADDED
        traceback.print_exc() # ADDED for detailed error
        logger.exception(f"Error generating summary for conversation {conversation_id}: {e}")
        try:
            db.session.rollback()
        except:
            pass

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
    """Get all conversations for the current user"""
    try:
        from models import Conversation
        
        # Log if this is a cache-busting request
        if request.args.get('_'):
            logger.info(f"Received cache-busting request for conversations at timestamp: {request.args.get('_')}")
        
        # Get all conversations, ordered by most recently updated first
        # Force a fresh query from the database (don't use cached results)
        db.session.expire_all()
        all_conversations = Conversation.query.filter_by(is_active=True).order_by(Conversation.updated_at.desc()).all()
        
        if not all_conversations:
            # Create a demo conversation if none exist
            title = "New Conversation"
            share_id = generate_share_id()
            conversation = Conversation(title=title, share_id=share_id)
            db.session.add(conversation)
            try:
                db.session.commit()
                logger.info("Created initial Demo Conversation")
                # Include created_at timestamp for proper date formatting in the UI
                conversations = [{"id": conversation.id, "title": conversation.title, "created_at": conversation.created_at.isoformat()}]
            except Exception as e:
                logger.exception("Error committing demo conversation")
                db.session.rollback()
                conversations = []
        else:
            # Convert all conversations to the format expected by the frontend
            # Include created_at date for proper date formatting in the UI
            conversations = [{"id": conv.id, "title": conv.title, "created_at": conv.created_at.isoformat()} for conv in all_conversations]
            
            # Log each conversation's details for debugging
            for conv in conversations:
                print(f"[CONVERSATIONS] ID: {conv['id']}, Title: '{conv['title']}', Created: {conv['created_at']}")
            
            logger.info(f"Returning {len(conversations)} conversations")

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
            # Always start with "New Conversation" title to allow for automatic title generation later
            title = "New Conversation"
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
                 
        # --- Incorporate document context from RAG system ---
        if ENABLE_RAG:
            try:
                # Get user ID for retrieving documents
                rag_user_id = str(current_user.id) if current_user and current_user.is_authenticated else get_user_identifier()
                logger.info(f"RAG: Attempting retrieval for user_id: {rag_user_id}, Query: '{user_message[:50]}...'")
                
                # Retrieve relevant document chunks with better error handling
                try:
                    # Check for Azure credentials before attempting to retrieve chunks
                    azure_key = os.environ.get('AZURE_OPENAI_API_KEY')
                    azure_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
                    azure_deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT')
                    
                    if not (azure_key and azure_endpoint and azure_deployment):
                        logger.error("RAG: Azure OpenAI credentials are missing or incomplete.")
                        logger.error("RAG: Ensure AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT are set.")
                        # Skip RAG retrieval when credentials are missing 
                        relevant_chunks = []
                    else:
                        relevant_chunks = document_processor.retrieve_relevant_chunks(
                            query_text=user_message,
                            user_id=rag_user_id,
                            limit=5  # Retrieve top 5 most relevant chunks
                        )
                        logger.info(f"RAG: Found {len(relevant_chunks)} relevant chunks using Azure embeddings.")
                except Exception as retrieval_error:
                    logger.error(f"RAG: Error retrieving document chunks: {retrieval_error}")
                    
                    # Check if this is a common MongoDB Atlas Vector Search issue
                    error_str = str(retrieval_error).lower()
                    if any(term in error_str for term in ["index not found", "vector search", "$vectorsearch"]):
                        logger.error("RAG: MongoDB Atlas Vector Search index may not be properly configured. " +
                                    "Create a vector search index named 'vector_index' on the 'memory.document_chunks' collection.")
                    elif "azure" in error_str or "openai" in error_str:
                        logger.error("RAG: Azure OpenAI embedding service error. Check API key, endpoint, and deployment name.")
                    
                    # Continue without RAG context
                    relevant_chunks = []
                    logger.info("RAG: Continuing without document context due to retrieval error.")
                
                if relevant_chunks and len(relevant_chunks) > 0:
                    # Format document chunks as context
                    context_text = "Below is relevant information from your documents:\n\n"
                    
                    for i, chunk in enumerate(relevant_chunks):
                        source = chunk.get('source_document_name', 'Unknown')
                        text = chunk.get('text_chunk', '')
                        score = chunk.get('score', 0)
                        
                        # Add formatted chunk with source attribution
                        context_text += f"[Document: {source}]\n{text}\n\n"
                    
                    logger.info(f"RAG: Formatted context text (first 100 chars): {context_text[:100]}...")
                    
                    # Add a context system message at the beginning of the conversation
                    context_message = {
                        "role": "system",
                        "content": (
                            "The following information from the user's documents is relevant to their question. "
                            "Use this information to provide accurate answers and refer to the sources when appropriate.\n\n"
                            f"{context_text}\n"
                            "If the user's question cannot be fully answered with the given context, "
                            "acknowledge what information you have and what might be missing."
                        )
                    }
                    
                    # Add context to the start of messages if message list is not empty
                    if len(messages) > 0:
                        # Check if the first message is already a system message
                        if messages[0].get('role') == 'system':
                            # Save original system message for logging
                            original_system = messages[0]['content']
                            
                            # Append context to existing system message
                            messages[0]['content'] = context_message['content'] + "\n\n" + original_system
                            
                            logger.info(f"RAG: Added context to existing system message. New length: {len(messages[0]['content'])}")
                        else:
                            # Insert new system message at the beginning
                            messages.insert(0, context_message)
                            logger.info(f"RAG: Inserted context as new system message at beginning. Messages count: {len(messages)}")
                    else:
                        # Just add the context message - this case should be rare
                        messages.insert(0, context_message)  # Use insert instead of append to ensure it's first
                        logger.info("RAG: Added context message to empty message list")
                    
                    # Log the structure of the messages array for debugging
                    try:
                        msg_roles = [f"{i}:{msg['role']}" for i, msg in enumerate(messages)]
                        logger.info(f"RAG: Message structure after adding context: {msg_roles}")
                    except Exception as e:
                        logger.error(f"RAG: Error logging message structure: {e}")
                    
                    logger.info(f"RAG: Added context from {len(relevant_chunks)} document chunks")
                else:
                    logger.info("No relevant document chunks found for the query")
                    
            except Exception as e:
                logger.error(f"Error incorporating RAG context: {e}")

        # --- Prepare Payload ---
        payload = {
            'model': openrouter_model,
            'messages': messages,
            'stream': True,
            'reasoning': {}  # Enable reasoning tokens for all models that support it
        }
        
        # --- ADD LOGGING FOR FINAL PROMPT ---
        try:
            # Use json.dumps for clean logging of the potentially large messages list
            final_messages_json = json.dumps(messages, indent=2)
            logger.debug(f"RAG DEBUG: Final messages list being sent to LLM:\n{final_messages_json}")
        except Exception as json_err:
            logger.error(f"RAG DEBUG: Error serializing messages for logging: {json_err}")
        # --- END OF ADDED LOGGING ---
        
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
                        
                        # Check if this is the first assistant message and generate a title
                        try:
                            # Count assistant messages in this conversation
                            assistant_count = Message.query.filter_by(
                                conversation_id=current_conv_id, 
                                role='assistant'
                            ).count()
                            
                            # If this is the first assistant message, trigger title generation
                            if assistant_count == 1:
                                logger.info(f"First assistant message detected for conversation {current_conv_id}. Triggering title generation.")
                                # Call the generate_summary function - non-blocking under gevent
                                # Ensure we've patched gevent beforehand to make this properly async
                                print(f"[CHAT] About to generate title for conversation {current_conv_id}")
                                try:
                                    generate_summary(current_conv_id)
                                    print(f"[CHAT] Title generation for conversation {current_conv_id} initiated successfully")
                                except Exception as e:
                                    import traceback
                                    print(f"[CHAT] Error initiating title generation: {e}")
                                    traceback.print_exc()
                        except Exception as e:
                            logger.error(f"Error checking message count or triggering title generation: {e}")
                            # Don't raise the exception - we want to continue even if this fails

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

@app.route('/api/rag/diagnostics', methods=['GET'])
def rag_diagnostics():
    """
    Diagnostic endpoint to check the state of RAG functionality.
    This helps identify issues with document storage and retrieval.
    """
    if not ENABLE_RAG:
        return jsonify({"error": "RAG functionality is not enabled"}), 400
        
    try:
        # Get user ID - use either authenticated user or session-based identifier
        if current_user and current_user.is_authenticated:
            user_id = str(current_user.id)
        else:
            user_id = get_user_identifier()
            
        # Run diagnostic checks
        diagnostics = document_processor.diagnostic_fetch_chunks(user_id)
        
        # Add some system information
        diagnostics["system_info"] = {
            "rag_enabled": ENABLE_RAG,
            "memory_enabled": ENABLE_MEMORY_SYSTEM,
            "azure_creds_available": all([
                os.environ.get('AZURE_OPENAI_API_KEY'),
                os.environ.get('AZURE_OPENAI_ENDPOINT'),
                os.environ.get('AZURE_OPENAI_DEPLOYMENT')
            ])
        }
        
        return jsonify(diagnostics)
    except Exception as e:
        logger.exception(f"Error in RAG diagnostics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_documents():
    """
    Route to handle document uploads for RAG functionality.
    Processes and stores documents in MongoDB for later retrieval.
    """
    if not ENABLE_RAG:
        return jsonify({"error": "RAG functionality is not enabled"}), 400
        
    try:
        # Get user ID - use either authenticated user or session-based identifier
        if current_user and current_user.is_authenticated:
            user_id = str(current_user.id)
        else:
            user_id = get_user_identifier()
            
        # Check if files were uploaded
        if 'files[]' not in request.files:
            return jsonify({"error": "No files were uploaded"}), 400
            
        files = request.files.getlist('files[]')
        if not files or len(files) == 0:
            return jsonify({"error": "No files were selected"}), 400
            
        # Define allowed file extensions based on our supported formats
        allowed_extensions = {
            '.txt', '.pdf', '.docx', '.md', '.html', '.htm', 
            '.json', '.yaml', '.yml', '.csv', '.tsv', '.rtf',
            '.srt', '.vtt', '.log', '.py', '.js', '.java', 
            '.c', '.cpp', '.cs', '.rb', '.php'
        }
        
        # Process each file
        results = []
        
        for file in files:
            if file.filename == '':
                results.append({"filename": "unnamed", "success": False, "message": "File has no name"})
                continue
                
            # Check file extension
            filename = file.filename
            ext = os.path.splitext(filename)[1].lower()
            
            if ext not in allowed_extensions:
                results.append({
                    "filename": filename,
                    "success": False,
                    "message": f"File type {ext} is not supported"
                })
                continue
                
            # Start a background thread to process the file
            def process_file_task(file_data, filename, user_id):
                logger.info(f"BACKGROUND TASK STARTED for {filename}, user {user_id}")
                try:
                    # Process and store the document
                    result = document_processor.process_and_store_document(file_data, filename, user_id)
                    logger.info(f"Document processing completed for {filename}: {result}")
                except Exception as e:
                    logger.exception(f"Error processing document {filename}: {e}")
                logger.info(f"BACKGROUND TASK FINISHED for {filename}, user {user_id}")
            
            # Create a copy of the file data for background processing
            file_data = file.stream.read()
            file_stream = io.BytesIO(file_data)
            
            # Start background processing
            processing_thread = threading.Thread(
                target=process_file_task,
                args=(file_stream, filename, user_id)
            )
            processing_thread.daemon = True  # Allow the thread to be terminated when the main program exits
            processing_thread.start()
            
            results.append({
                "filename": filename,
                "success": True,
                "message": "Processing started in background"
            })
        
        return jsonify({
            "success": True,
            "message": f"Processing {len(files)} documents in the background",
            "results": results
        })
        
    except Exception as e:
        logger.exception(f"Error handling document upload: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# --- Main Execution ---
if __name__ == '__main__':
    logger.info("Starting Flask development server")
    # Use debug=False if running with Gunicorn/Uvicorn in production
    # The threaded=True option might offer slightly better handling of concurrent requests
    # for the dev server compared to the default, but Gunicorn handles concurrency differently.
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)