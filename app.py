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
import datetime
import mimetypes
from pathlib import Path
from PIL import Image  # For image processing
from flask import Flask, render_template, request, Response, session, jsonify, abort, url_for, redirect, flash, stream_with_context, send_from_directory # Added send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, current_user, login_required
from azure.storage.blob import BlobServiceClient, ContentSettings  # For Azure Blob Storage

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

# Initialize Azure Blob Storage for image uploads
try:
    # Get connection string and container name from environment variables
    azure_connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    azure_container_name = os.environ.get("AZURE_STORAGE_CONTAINER_NAME")
    
    if not azure_connection_string or not azure_container_name:
        raise ValueError("Missing Azure Storage credentials")
        
    # Create the BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(azure_connection_string)
    
    # Get a client to interact with the container
    container_client = blob_service_client.get_container_client(azure_container_name)
    
    # Check if container exists, if not create it
    try:
        container_properties = container_client.get_container_properties()
        logger.info(f"Container {azure_container_name} exists")
    except Exception as container_error:
        logger.info(f"Container {azure_container_name} does not exist, creating it...")
        container_client = blob_service_client.create_container(azure_container_name)
        logger.info(f"Container {azure_container_name} created successfully")
    
    # Validate by trying to list blobs
    container_client.list_blobs(max_results=1)
    
    logger.info(f"Azure Blob Storage initialized successfully for container: {azure_container_name}")
    USE_AZURE_STORAGE = True
except Exception as e:
    logger.warning(f"Failed to initialize Azure Blob Storage: {e}")
    logger.info("Falling back to local storage for image uploads")
    USE_AZURE_STORAGE = False


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

# Multimodal models that support image inputs
MULTIMODAL_MODELS = [
    "google/gemini-2.5-pro-preview-03-25",
    "google/gemini-2.5-flash-preview-03-25",
    "anthropic/claude-3.7-sonnet", 
    "anthropic/claude-3.7-haiku",
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-sonnet", 
    "anthropic/claude-3-opus",
    "openai/gpt-4o", 
    "openai/gpt-4-turbo", 
    "openai/gpt-4-vision"
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

def get_object_storage_url(object_name, public=True, expires_in=3600):
    """
    Generate a URL for an object in Azure Blob Storage.
    
    Args:
        object_name (str): The name of the object
        public (bool): Whether to generate a public URL or a signed URL
        expires_in (int): The number of seconds the signed URL is valid for
        
    Returns:
        str: The URL for the object
    """
    try:
        # Check if Azure Blob Storage is properly initialized
        if not ('USE_AZURE_STORAGE' in globals() and USE_AZURE_STORAGE and 
                'container_client' in globals() and container_client):
            logger.warning("Azure Blob Storage not initialized, cannot generate URL")
            return None
            
        if public:
            # For public access, use the blob's URL directly
            blob_client = container_client.get_blob_client(object_name)
            return blob_client.url
        else:
            # Generate a SAS token for time-limited access
            blob_client = container_client.get_blob_client(object_name)
            
            # Generate SAS token that's valid for "expires_in" seconds
            from datetime import datetime, timedelta
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions
            
            # Get account information from connection string
            account_name = None
            account_key = None
            
            # Get connection string from environment again to be safe
            azure_connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
            azure_container_name = os.environ.get("AZURE_STORAGE_CONTAINER_NAME")
            
            if not azure_connection_string or not azure_container_name:
                logger.error("Missing Azure Storage credentials")
                return None
            
            # Parse connection string to extract account name and key
            # Connection string format: DefaultEndpointsProtocol=https;AccountName=xxx;AccountKey=xxx;EndpointSuffix=core.windows.net
            conn_str_parts = azure_connection_string.split(';')
            for part in conn_str_parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    if key.lower() == 'accountname':
                        account_name = value
                    elif key.lower() == 'accountkey':
                        account_key = value
            
            if not account_name or not account_key:
                logger.error("Unable to extract account information from connection string")
                return None
                
            # Generate SAS token with broad permissions for browser access
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=azure_container_name,
                blob_name=object_name,
                account_key=account_key,
                # Add list permission to help with CORS issues
                permission=BlobSasPermissions(read=True, list=True),
                # Long expiry to prevent issues with time syncing
                expiry=datetime.utcnow() + timedelta(seconds=expires_in),
                # Add start time slightly in the past to account for clock skew
                start=datetime.utcnow() - timedelta(minutes=5),
                # Add cache control to the SAS token
                cache_control="public, max-age=3600"
            )
            
            # Return the full URL with SAS token
            return f"{blob_client.url}?{sas_token}"
    except Exception as e:
        logger.exception(f"Error generating Azure Blob Storage URL: {e}")
        return None

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test-upload')
def test_upload_page():
    """
    A simple route to test the image upload functionality.
    This serves a static HTML page for testing without requiring the full UI.
    """
    return send_from_directory('static', 'test_upload.html')

@app.route('/upload_image', methods=['POST'])
def upload_image():
    """
    Route to handle image uploads for multimodal messages.
    Processes, resizes if needed, and stores images in Azure Blob Storage.
    
    Examples:
        # Success case - uploading a valid image
        curl -X POST -F "file=@/path/to/image.jpg" http://localhost:5000/upload_image
        
        # Failure case - no file provided
        curl -X POST http://localhost:5000/upload_image
        
        # Failure case - unsupported file type
        curl -X POST -F "file=@/path/to/document.txt" http://localhost:5000/upload_image
        
    Success Response:
        {
            "success": true,
            "image_url": "https://gloriamundoblobs.blob.core.windows.net/gloriamundoblobs/a1b2c3d4e5f6.jpg"
        }
        
    Error Response:
        {
            "error": "No file provided"
        }
        
        or
        
        {
            "error": "File type .txt is not supported. Please upload an image in jpg, png, gif, or webp format."
        }
    """
    try:
        # Verify a file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
            
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({"error": "No file selected"}), 400
            
        # Validate file type
        filename = file.filename
        extension = Path(filename).suffix.lower()
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        
        if extension not in allowed_extensions:
            return jsonify({
                "error": f"File type {extension} is not supported. Please upload an image in jpg, png, gif, or webp format."
            }), 400
            
        # Generate a unique filename to avoid collisions
        unique_filename = f"{uuid.uuid4().hex}{extension}"
        
        # Process image - resize if too large
        max_dimension = 1024  # Maximum width or height
        
        # Read the image into memory
        image_data = file.read()
        image_stream = io.BytesIO(image_data)
        processed_image_stream = io.BytesIO()
        
        try:
            with Image.open(image_stream) as img:
                # Check dimensions
                width, height = img.size
                if width > max_dimension or height > max_dimension:
                    # Calculate new dimensions maintaining aspect ratio
                    if width > height:
                        new_width = max_dimension
                        new_height = int(height * (max_dimension / width))
                    else:
                        new_height = max_dimension
                        new_width = int(width * (max_dimension / height))
                    
                    # Resize the image
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                
                # Get the MIME type for the content type
                mime_type = mimetypes.guess_type(filename)[0] or 'image/jpeg'
                
                # Save the processed image to memory stream
                img.save(processed_image_stream, format=img.format or 'JPEG')
                processed_image_stream.seek(0)
                logger.info(f"Processed image to dimensions: {img.width}x{img.height}")
        except Exception as e:
            logger.exception(f"Error processing image: {e}")
            # If processing fails, use the original image data
            processed_image_stream = io.BytesIO(image_data)
            processed_image_stream.seek(0)
            mime_type = mimetypes.guess_type(filename)[0] or 'image/jpeg'
            logger.info(f"Using original image due to processing error")
        
        # Storage path for Azure Blob Storage
        storage_path = unique_filename
        
        # Store the image in Azure Blob Storage or fallback to local storage
        if 'USE_AZURE_STORAGE' in globals() and USE_AZURE_STORAGE and 'container_client' in globals() and container_client:
            try:
                # Get image data from the processed stream
                processed_image_stream.seek(0)
                image_data = processed_image_stream.read()
                
                # Create a blob client for the specific blob
                blob_client = container_client.get_blob_client(storage_path)
                
                # Set content settings (MIME type) with additional browser-friendly headers
                content_settings = ContentSettings(
                    content_type=mime_type,
                    # Set Cache-Control to allow caching but require validation
                    cache_control="public, max-age=3600",
                    # Set Content-Disposition to inline to encourage browsers to display it
                    content_disposition="inline"
                )
                
                # Upload the image data to Azure Blob Storage
                blob_client.upload_blob(
                    data=image_data,
                    content_settings=content_settings,
                    overwrite=True
                )
                
                # Generate a URL with SAS token for the uploaded image (7 days expiry)
                image_url = get_object_storage_url(object_name=storage_path, public=False, expires_in=7*24*3600)
                # Log debugging information
                logger.info(f"Uploaded image to Azure Blob Storage with URL: {image_url[:50]}...")
                
                # Verify the URL is generated
                if not image_url:
                    logger.error("Failed to generate URL for Azure Blob Storage")
                    raise ValueError("Failed to generate URL for uploaded image")
            except Exception as e:
                logger.exception(f"Error uploading to Azure Blob Storage: {e}")
                # Fallback to local storage if Azure Blob Storage fails
                upload_dir = Path('static/uploads')
                upload_dir.mkdir(parents=True, exist_ok=True)
                file_path = upload_dir / unique_filename
                
                with open(file_path, 'wb') as f:
                    processed_image_stream.seek(0)
                    f.write(processed_image_stream.read())
                
                image_url = url_for('static', filename=f'uploads/{unique_filename}', _external=True)
                logger.info(f"Fallback: Saved image to local filesystem: {file_path}")
        else:
            # Azure Blob Storage not available, use local filesystem
            upload_dir = Path('static/uploads')
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / unique_filename
            
            with open(file_path, 'wb') as f:
                processed_image_stream.seek(0)
                f.write(processed_image_stream.read())
            
            image_url = url_for('static', filename=f'uploads/{unique_filename}', _external=True)
            logger.info(f"Saved image to local filesystem: {file_path}")
        
        return jsonify({
            "success": True,
            "image_url": image_url
        })
        
    except Exception as e:
        logger.exception(f"Error handling image upload: {e}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

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
        # Get optional image URL for multimodal messages
        image_url = data.get('image_url', None)
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
            conversation_id=conversation.id, 
            role='user', 
            content=user_message,
            image_url=image_url  # Save image URL if provided
        )
        db.session.add(user_db_message)
        try:
             db.session.commit()
             logger.info(f"Saved user message {user_db_message.id} for conversation {conversation.id}")
             # Log if multimodal content was included
             if image_url:
                logger.info(f"Image URL saved with message: {image_url[:50]}...")
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

        # Load conversation history from database
        db_messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
        for msg in db_messages:
             if msg.id != user_db_message.id: 
                 # Only include text content for history messages (not their images)
                 messages.append({'role': msg.role, 'content': msg.content})

        # Format the current user message, possibly with image
        # Check if this is a multimodal message (has image) and model supports it
        if image_url and openrouter_model in MULTIMODAL_MODELS:
            # Different models require different formatting for multimodal messages
            if 'claude' in openrouter_model.lower():
                # Claude format
                user_content = [
                    {"type": "text", "text": user_message},
                    {"type": "image", "source": {"url": image_url}}
                ]
                messages.append({'role': 'user', 'content': user_content})
                logger.info(f"Added multimodal message with Claude-format image to {openrouter_model}")
            elif 'gpt-4' in openrouter_model.lower() or 'gpt4' in openrouter_model.lower():
                # OpenAI GPT-4 format
                user_content = [
                    {"type": "text", "text": user_message},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
                messages.append({'role': 'user', 'content': user_content})
                logger.info(f"Added multimodal message with OpenAI-format image to {openrouter_model}")
            elif 'gemini' in openrouter_model.lower():
                # Google Gemini format
                user_content = [
                    {"type": "text", "text": user_message},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
                messages.append({'role': 'user', 'content': user_content})
                logger.info(f"Added multimodal message with Gemini-format image to {openrouter_model}")
            else:
                # Generic format as fallback
                user_content = [
                    {"type": "text", "text": user_message},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
                messages.append({'role': 'user', 'content': user_content})
                logger.info(f"Added multimodal message with generic-format image to {openrouter_model}")
                
            # Log the actual URL being sent
            logger.info(f"Image URL sent to model: {image_url}")
        else:
            # Standard text-only message
            messages.append({'role': 'user', 'content': user_message})
            
            # Log if image was provided but model doesn't support it
            if image_url and openrouter_model not in MULTIMODAL_MODELS:
                logger.warning(f"Image URL provided but model {openrouter_model} doesn't support multimodal input. Image ignored.")

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


@app.route('/conversation/<int:conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    """ Get all messages for a specific conversation """
    try:
        from models import Conversation, Message 
        
        # Check if conversation exists
        conversation = db.session.get(Conversation, conversation_id)
        if not conversation:
            abort(404, description="Conversation not found")
            
        # Get all messages for this conversation, ordered by creation time
        messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
        
        # Format messages for the frontend
        formatted_messages = []
        for msg in messages:
            formatted_message = {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "rating": msg.rating,
                "model": msg.model
            }
            formatted_messages.append(formatted_message)
            
        logger.info(f"Returning {len(formatted_messages)} messages for conversation {conversation_id}")
        return jsonify({
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat()
            },
            "messages": formatted_messages
        })
    except Exception as e:
        logger.exception(f"Error getting messages for conversation {conversation_id}")
        return jsonify({"error": str(e)}), 500

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

@app.route('/api/memory/diagnostics', methods=['GET'])
def memory_diagnostics():
    """
    Diagnostic endpoint to check the state of the Chatbot Memory System.
    This helps identify issues with the long-term memory component using vector embeddings.
    """
    if not ENABLE_MEMORY_SYSTEM:
        return jsonify({"error": "Memory system is not enabled"}), 400
        
    try:
        # Get user ID - use either authenticated user or session-based identifier
        if current_user and current_user.is_authenticated:
            user_id = str(current_user.id)
        else:
            user_id = get_user_identifier()
        
        # Import the memory manager here to avoid circular imports
        from memory_integration import get_memory_manager
        memory_manager = get_memory_manager()
        
        if not memory_manager:
            return jsonify({"error": "Memory manager failed to initialize"}), 500
            
        # Prepare diagnostics object
        diagnostics = {
            "system_info": {
                "memory_enabled": ENABLE_MEMORY_SYSTEM,
                "rag_enabled": ENABLE_RAG,
                "vector_search_refactored": True,  # Flag to indicate refactored implementation
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "azure_creds_available": all([
                    os.environ.get('AZURE_OPENAI_API_KEY'),
                    os.environ.get('AZURE_OPENAI_ENDPOINT'),
                    os.environ.get('AZURE_OPENAI_DEPLOYMENT')
                ]),
                "vector_search_info": {
                    "index_name": "memory_vector_index",
                    "collection": "user_profiles",
                    "embedding_path": "preferences_embeddings.embedding",
                    "dimensions": 3072,
                    "notes": "The MongoDB Atlas vector search index must be created manually in the Atlas console."
                }
            }
        }
        
        # Test embedding generation
        try:
            test_text = "This is a test embedding for memory system diagnostics."
            logger.info(f"MEMORY_DIAG: Generating test embedding")
            start_time = time.time()
            test_embedding = memory_manager._get_embedding(test_text)
            embed_time = time.time() - start_time
            
            if test_embedding:
                diagnostics["embedding_test"] = {
                    "status": "success",
                    "dimensions": len(test_embedding),
                    "time_seconds": round(embed_time, 2),
                    "sample_values": test_embedding[:3],  # Just show first few values
                }
            else:
                diagnostics["embedding_test"] = {
                    "status": "failed",
                    "error": "Embedding generation returned None"
                }
        except Exception as embed_err:
            logger.error(f"MEMORY_DIAG: Embedding test failed: {embed_err}")
            diagnostics["embedding_test"] = {
                "status": "error",
                "error": str(embed_err)
            }
            
        # Check for MongoDB collections
        try:
            # Get counts and sample documents for chat_sessions
            chat_sessions_count = memory_manager.chat_sessions.count_documents({})
            user_profile_count = memory_manager.user_profiles.count_documents({})
            
            # Count documents with both field names
            user_id_count = memory_manager.user_profiles.count_documents({"user_id": {"$exists": True}})
            userId_count = memory_manager.user_profiles.count_documents({"userId": {"$exists": True}})
            both_fields_count = memory_manager.user_profiles.count_documents({
                "$and": [
                    {"user_id": {"$exists": True}},
                    {"userId": {"$exists": True}}
                ]
            })
            
            # Get a sample of each
            sample_chat_session = memory_manager.chat_sessions.find_one(
                {}, 
                {"_id": 0, "user_id": 1, "userId": 1, "session_id": 1, "created_at": 1, "message_history": {"$slice": 1}}
            )
            
            sample_user_profile = memory_manager.user_profiles.find_one(
                {}, 
                {"_id": 0, "user_id": 1, "userId": 1, "created_at": 1, "facts": 1, 
                 "preferences_embeddings": {"$slice": 1}}
            )
            
            # Format dates for JSON serialization
            if sample_chat_session and "created_at" in sample_chat_session:
                sample_chat_session["created_at"] = sample_chat_session["created_at"].isoformat()
                
            if sample_user_profile and "created_at" in sample_user_profile:
                sample_user_profile["created_at"] = sample_user_profile["created_at"].isoformat()
                
            # Add collection data to diagnostics
            diagnostics["collections"] = {
                "chat_sessions": {
                    "count": chat_sessions_count,
                    "sample": sample_chat_session
                },
                "user_profiles": {
                    "count": user_profile_count,
                    "user_id_field_count": user_id_count,
                    "userId_field_count": userId_count,
                    "both_fields_count": both_fields_count,
                    "sample": sample_user_profile
                }
            }
        except Exception as mongo_err:
            logger.error(f"MEMORY_DIAG: MongoDB collection check failed: {mongo_err}")
            diagnostics["collections"] = {
                "status": "error",
                "error": str(mongo_err)
            }
            
        # Test long-term memory retrieval with the current user
        try:
            logger.info(f"MEMORY_DIAG: Testing long-term memory retrieval for user {user_id}")
            start_time = time.time()
            memory_result = memory_manager.retrieve_long_term_memory(
                user_id=user_id,
                query_text="Test query for diagnostics",
                vector_search_limit=2
            )
            retrieve_time = time.time() - start_time
            
            # Format the results for display
            facts_count = len(memory_result.get("matching_facts", {}))
            prefs_count = len(memory_result.get("similar_preferences", []))
            
            diagnostics["memory_retrieval_test"] = {
                "status": "success",
                "time_seconds": round(retrieve_time, 2),
                "facts_count": facts_count,
                "preferences_count": prefs_count,
                "sample_facts": list(memory_result.get("matching_facts", {}).keys())[:5],
                "sample_preferences": [p.get("text", "") for p in memory_result.get("similar_preferences", [])][:2]
            }
        except Exception as retrieve_err:
            logger.error(f"MEMORY_DIAG: Memory retrieval test failed: {retrieve_err}")
            diagnostics["memory_retrieval_test"] = {
                "status": "error",
                "error": str(retrieve_err)
            }
        
        return jsonify(diagnostics)
    except Exception as e:
        logger.exception(f"Error in memory diagnostics: {e}")
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
    # ensure gevent monkey-patching already happened at import time
    app.run(host='0.0.0.0', port=5000, debug=True)