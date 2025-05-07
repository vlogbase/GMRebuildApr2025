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
import atexit
import traceback
import sys
from pathlib import Path
from PIL import Image  # For image processing
from flask import Flask, render_template, request, Response, session, jsonify, abort, url_for, redirect, flash, stream_with_context, send_from_directory # Added send_from_directory
from urllib.parse import urlparse # For URL analysis in image handling
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_wtf.csrf import CSRFProtect
from azure.storage.blob import BlobServiceClient, ContentSettings  # For Azure Blob Storage
from apscheduler.schedulers.background import BackgroundScheduler
from price_updater import fetch_and_store_openrouter_prices, model_prices_cache

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

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Add global template context variables
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

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
login_manager.login_view = 'login'

# Register blueprints
try:
    from google_auth import google_auth
    app.register_blueprint(google_auth)
    logger.info("Google Auth blueprint registered successfully")
except Exception as e:
    logger.error(f"Error registering Google Auth blueprint: {e}")

# Register billing blueprint
try:
    from billing import billing_bp
    app.register_blueprint(billing_bp, url_prefix='/billing')
    # Exempt Stripe webhook from CSRF protection
    csrf.exempt('billing.stripe_webhook')
    logger.info("Billing blueprint registered successfully with prefix /billing")
except Exception as e:
    logger.error(f"Error registering Billing blueprint: {e}")

# Register affiliate blueprint
try:
    from affiliate import affiliate_bp
    app.register_blueprint(affiliate_bp, url_prefix='/affiliate')
    logger.info("Affiliate blueprint registered successfully with prefix /affiliate")
except Exception as e:
    logger.error(f"Error registering Affiliate blueprint: {e}")

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
    # Updated with verified model IDs that exist in OpenRouter
    "gemini-pro": "google/gemini-pro",
    "gemini-pro-vision": "google/gemini-pro-vision",
    "claude-3-opus": "anthropic/claude-3-opus-20240229",
    "claude-3-sonnet": "anthropic/claude-3-sonnet-20240229",
    "claude-3-haiku": "anthropic/claude-3-haiku-20240307",
    "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet-20240620",
    "claude-3.7-sonnet": "anthropic/claude-3.7-sonnet-20240910",
    "gpt-4-turbo": "openai/gpt-4-turbo",
    "gpt-4-vision": "openai/gpt-4-vision-preview",
    "gpt-4o": "openai/gpt-4o-2024-05-13",
    "mistral-large": "mistralai/mistral-large-latest",
    "llama-3-8b": "meta-llama/llama-3-8b",
    "free-gemini": "google/gemini-flash:free" # Verified free model
}
DEFAULT_PRESET_MODELS = {
    # Updated preset models with verified available IDs
    "1": "google/gemini-pro-vision", # Default multimodal model
    "2": "anthropic/claude-3-haiku-20240307", # Fast, good quality
    "3": "anthropic/claude-3-sonnet-20240229", # High quality
    "4": "openai/gpt-4o-2024-05-13", # Premium quality
    "5": "meta-llama/llama-3-8b", # Open model
    "6": "google/gemini-flash:free" # Free model
}
FREE_MODEL_FALLBACKS = [
    # Updated with verified free models available in OpenRouter
    "google/gemini-flash:free",  # Primary free model
    "meta-llama/llama-3-8b-free", # Fallback free model
    "openrouter/auto:free",     # Auto-selection free model
    "neural-chat/neural-chat-7b-v3-1:free" # Another fallback
]

# Multimodal models that support image inputs
MULTIMODAL_MODELS = [
    # Verified specific model IDs - full matches for maximum reliability
    "anthropic/claude-3-opus-20240229",
    "anthropic/claude-3-sonnet-20240229",
    "anthropic/claude-3-haiku-20240307",
    "anthropic/claude-3.5-sonnet-20240620",
    "anthropic/claude-3.7-sonnet-20240910",
    "openai/gpt-4-vision-preview",
    "openai/gpt-4o-2024-05-13",
    "openai/gpt-4-turbo",
    
    # Google model IDs as currently available in OpenRouter
    "google/gemini-pro-vision",
    "google/gemini-1.0-pro-vision",
    "google/gemini-1.0-pro-vision-001",
    "google/gemini-pro",
    
    # Generic model patterns - these partial matches help catch model variations
    # Put these after specific matches for better visibility
    "google/gemini",  # This will match all Gemini models
    "anthropic/claude-3", # This will match all Claude 3 models
    "claude-3",
    "claude-3.5",
    "claude-3.7",
    "gpt-4-vision",
    "gpt-4o",
    "vision",
    "multimodal"
]

# Safe fallback model IDs when no specific model can be determined
# Listed in order of preference - we'll try each one until we find one that works
SAFE_FALLBACK_MODELS = [
    "anthropic/claude-3-haiku-20240307",  # Most reliable and fast multimodal model
    "google/gemini-pro-vision",  # Good multimodal alternative
    "meta-llama/llama-3-8b",  # Text-only fallback
    "mistralai/mistral-7b"     # Another text-only fallback
]

# Cache for OpenRouter models
OPENROUTER_MODELS_CACHE = {
    "data": None,
    "timestamp": 0,
    "expiry": 86400  # Cache expiry in seconds (24 hours)
}

# This is needed for the non-authenticated user check in the chat endpoint
OPENROUTER_MODELS_INFO = []

# Initialize the scheduler for background tasks with enhanced configuration
def init_scheduler():
    """
    Initialize and start the background scheduler for periodic tasks.
    Returns the scheduler instance or None if it failed to start.
    
    This improved implementation ensures that:
    1. The scheduler is configured for maximum reliability in a web environment
    2. Jobs are properly registered and tracked
    3. The scheduler is actually running before returning
    4. Failed jobs can be retried
    """
    logger.info("Initializing background scheduler...")
    import traceback  # Import here to ensure availability
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
    
    try:
        # Import the price updater function
        from price_updater import fetch_and_store_openrouter_prices
        
        # Create scheduler with enhanced config for better reliability in web environments
        scheduler = BackgroundScheduler(
            daemon=True,
            job_defaults={
                'coalesce': True,  # Combine missed runs
                'max_instances': 1,  # Only one instance of a job can run at a time
                'misfire_grace_time': 300,  # Allow jobs to be 5 minutes late
                'max_runs': None,  # No limit on number of runs
            },
            timezone='UTC'  # Explicitly set timezone to avoid system timezone issues
        )
        
        # Add the OpenRouter price fetching job with enhanced configuration
        scheduler.add_job(
            func=fetch_and_store_openrouter_prices, 
            trigger='interval', 
            minutes=30,  
            id='fetch_model_prices_job',
            replace_existing=True,  # Replace if job already exists
            max_instances=1,  # Ensure only one instance runs
            jitter=120  # Add random jitter (in seconds) to avoid thundering herd
        )
        
        # Run the price fetching job immediately at scheduler startup to ensure we have fresh data
        scheduler.add_job(
            func=fetch_and_store_openrouter_prices,
            trigger='date',  # Run once at a specific time
            run_date=datetime.datetime.now() + datetime.timedelta(seconds=15),  # Run 15 seconds after startup
            id='initial_fetch_model_prices_job',
            replace_existing=True,
            max_instances=1
        )
        
        # Add scheduler event listeners to better track job execution
        def job_executed_event(event):
            job_id = event.job_id
            logger.info(f"Scheduler job {job_id} executed successfully")
            
        def job_error_event(event):
            job_id = event.job_id
            exception = event.exception
            traceback_str = event.traceback
            logger.error(f"Scheduler job {job_id} failed with error: {exception}")
            logger.error(f"Job error traceback: {traceback_str}")
            
            # For critical jobs like model price fetching, we can add automatic retry logic here
            if job_id == 'fetch_model_prices_job':
                logger.info(f"Scheduling retry for failed job {job_id} in 5 minutes")
                scheduler.add_job(
                    func=fetch_and_store_openrouter_prices,
                    trigger='date',
                    run_date=datetime.datetime.now() + datetime.timedelta(minutes=5),
                    id='retry_fetch_model_prices_job',
                    replace_existing=True
                )
        
        # Add the listeners to the scheduler
        scheduler.add_listener(job_executed_event, EVENT_JOB_EXECUTED)
        scheduler.add_listener(job_error_event, EVENT_JOB_ERROR)
        
        # Start the scheduler with enhanced error handling
        try:
            scheduler.start()
            logger.info("Background scheduler started successfully")
            
            # Wait a short time to verify the scheduler has started properly
            time.sleep(0.5)
            
            # Verify scheduler is running and has jobs
            if scheduler.running:
                all_jobs = scheduler.get_jobs()
                job_ids = [job.id for job in all_jobs]
                logger.info(f"Confirmed scheduler is running with jobs: {job_ids}")
                
                # Run a check on the job state
                job = scheduler.get_job('fetch_model_prices_job')
                if job:
                    logger.info(f"Model price fetch job scheduled, next run at: {job.next_run_time}")
                else:
                    logger.warning("Model price fetch job not found in scheduler!")
                    # Attempt to re-add the job if it's missing
                    scheduler.add_job(
                        func=fetch_and_store_openrouter_prices, 
                        trigger='interval', 
                        minutes=30, 
                        id='fetch_model_prices_job',
                        replace_existing=True
                    )
                
                return scheduler
            else:
                logger.error("Scheduler failed to start properly - running flag is False")
                return None
                
        except Exception as start_error:
            logger.error(f"Failed to start background scheduler: {start_error}")
            logger.error(traceback.format_exc())
            return None
            
    except ImportError as import_error:
        logger.error(f"Failed to import required modules for scheduler: {import_error}")
        logger.error(traceback.format_exc())
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error initializing scheduler: {e}")
        logger.error(traceback.format_exc())
        return None

# We don't need to define our own model fetching function here anymore
# Replaced by the consolidated fetch_and_store_openrouter_prices function from price_updater.py
# which now handles both pricing and model data in one place

# Initialize scheduler with improved implementation
scheduler = init_scheduler()
if not scheduler or not scheduler.running:
    logger.critical("Failed to initialize the scheduler! This may affect model data availability.")

# Initial fetch of model data at startup - crucial for application functionality
logger.info("Performing initial fetch of OpenRouter models at startup")
try:
    # First ensure proper Python imports
    import traceback
    from price_updater import fetch_and_store_openrouter_prices
    
    # Attempt to fetch model prices directly (which includes model info)
    # This bypasses the scheduler to ensure we get data at startup
    logger.info("Fetching initial model data directly...")
    price_success = fetch_and_store_openrouter_prices()
    if price_success:
        logger.info("Successfully fetched initial model prices including model information")
        # With prices loaded, we should also have models
    else:
        # If that fails, log a warning - we'll rely on the scheduler to retry soon
        logger.warning("Initial price fetching failed. The scheduler will retry shortly.")
        # Create a fallback model list for minimal functionality
        fallback_models = _generate_fallback_model_data()
        
    # Verify we have model data
    if OPENROUTER_MODELS_INFO and len(OPENROUTER_MODELS_INFO) > 0:
        logger.info(f"Initial model data fetch completed. {len(OPENROUTER_MODELS_INFO)} models available.")
    else:
        logger.warning("Initial model fetch completed but NO MODELS WERE RETURNED OR STORED!")
        # Initialize to empty array to avoid potential NoneType errors
        OPENROUTER_MODELS_INFO = [] 
        logger.warning("Setting OPENROUTER_MODELS_INFO to empty array to avoid NoneType errors")
        
except Exception as e:
    logger.error(f"Critical error fetching model data at startup: {e}")
    logger.error(traceback.format_exc())
    # Initialize to empty array to avoid potential NoneType errors
    OPENROUTER_MODELS_INFO = []
    logger.warning("Setting OPENROUTER_MODELS_INFO to empty array to avoid NoneType errors")

# Register scheduler shutdown with app exit
@atexit.register
def shutdown_scheduler():
    if scheduler and hasattr(scheduler, 'shutdown'):
        try:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")
    else:
        logger.warning("No active scheduler to shut down")

# --- Helper Functions ---
def get_user_identifier():
    if current_user and current_user.is_authenticated:
        # Return authenticated user's ID
        return f"user_{current_user.id}"

    # For non-authenticated users, use a temporary session ID
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
            'temperature': 0.7,  # Slightly creative but not too random
            'include_reasoning': True  # Enable reasoning tokens for better title generation
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

def _generate_fallback_model_data():
    """
    Generate fallback model data when OpenRouter API is unavailable.
    This ensures the frontend can still function with essential models.
    """
    logger.warning("Generating fallback model data with minimal functional models")
    
    # Create a minimal set of models to ensure the UI functions
    fallback_models = [
        {
            "id": "anthropic/claude-3-haiku",
            "name": "Claude 3 Haiku",
            "description": "Fast and efficient for everyday tasks, providing impressive reasoning capabilities at an affordable price.",
            "context_length": 200000,
            "pricing": {"prompt": 0.25, "completion": 1.25},
            "is_free": False,
            "is_multimodal": True,
            "is_reasoning": True,
            "is_perplexity": False
        },
        {
            "id": "anthropic/claude-3-opus",
            "name": "Claude 3 Opus",
            "description": "Most powerful Claude model for complex tasks requiring deep analysis, comprehension, coding, and reasoning.",
            "context_length": 200000,
            "pricing": {"prompt": 15.00, "completion": 75.00},
            "is_free": False,
            "is_multimodal": True,
            "is_reasoning": True,
            "is_perplexity": False
        },
        {
            "id": "google/gemini-1.5-pro",
            "name": "Gemini 1.5 Pro",
            "description": "Enhanced Google model with strong reasoning, comprehension, and code generation.",
            "context_length": 1000000,
            "pricing": {"prompt": 3.50, "completion": 10.00},
            "is_free": False,
            "is_multimodal": True,
            "is_reasoning": True,
            "is_perplexity": False
        },
        {
            "id": "google/gemini-2.0-flash-exp:free",
            "name": "Gemini 2.0 Flash (Free)",
            "description": "Very fast Google model with efficient processing for everyday tasks.",
            "context_length": 128000,
            "pricing": {"prompt": 0.00, "completion": 0.00},
            "is_free": True,
            "is_multimodal": True,
            "is_reasoning": False,
            "is_perplexity": False
        },
        {
            "id": "openai/gpt-4-turbo",
            "name": "GPT-4 Turbo",
            "description": "Optimized GPT-4 model for faster performance and balanced between speed and capability.",
            "context_length": 128000,
            "pricing": {"prompt": 10.00, "completion": 30.00},
            "is_free": False,
            "is_multimodal": False,
            "is_reasoning": True,
            "is_perplexity": False
        },
        {
            "id": "perplexity/sonar-small",
            "name": "Perplexity Sonar Small",
            "description": "Fast perplexity model good for tasks that require current information and web comprehension.",
            "context_length": 12000,
            "pricing": {"prompt": 1.00, "completion": 5.00},
            "is_free": False,
            "is_multimodal": False,
            "is_reasoning": False,
            "is_perplexity": True
        }
    ]
    
    # Update the global model info with these fallback models
    global OPENROUTER_MODELS_INFO
    OPENROUTER_MODELS_INFO = fallback_models
    
    # Also update the model cache for completeness
    result_data = {"data": fallback_models}
    if 'OPENROUTER_MODELS_CACHE' in globals():
        OPENROUTER_MODELS_CACHE["data"] = result_data
        OPENROUTER_MODELS_CACHE["timestamp"] = time.time()
    
    logger.info(f"Initialized with {len(fallback_models)} fallback models")
    return fallback_models

def generate_share_id(length=12):
    random_bytes = secrets.token_bytes(length)
    share_id = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    share_id = share_id.replace('=', '')[:length]
    return share_id

def get_object_storage_url(object_name, public=True, expires_in=3600, clean_url=False, model_name=None):
    """
    Generate a URL for an object in Azure Blob Storage.
    This function creates URLs that are compatible with OpenRouter's multimodal API requirements.
    
    Args:
        object_name (str): The name of the object
        public (bool): Whether to generate a public URL or a signed URL
        expires_in (int): The number of seconds the signed URL is valid for
        clean_url (bool): If True, generate a URL without query parameters (better for Gemini)
        model_name (str): Optional model name to generate model-specific URLs
        
    Returns:
        str: The URL for the object that can be used in multimodal AI messages
    """
    try:
        # Check if Azure Blob Storage is properly initialized
        if not ('USE_AZURE_STORAGE' in globals() and USE_AZURE_STORAGE and 
                'container_client' in globals() and container_client):
            logger.warning("Azure Blob Storage not initialized, cannot generate URL")
            return None
        
        # Check if using a model that needs special handling (like Gemini)
        is_gemini = model_name and "gemini" in model_name.lower()
        
        # If Gemini model is specified, force clean_url to True as Gemini often has issues with SAS tokens
        if is_gemini:
            clean_url = True
            logger.info(f"Gemini model detected ({model_name}). Using clean URL without query parameters.")
            
        # For public access or clean URLs (for Gemini compatibility), use the blob's URL directly
        if public or clean_url:
            # Get a direct URL without any SAS token or query parameters
            blob_client = container_client.get_blob_client(object_name)
            clean_blob_url = blob_client.url
            logger.info(f"Generated clean URL without query parameters: {clean_blob_url[:100]}...")
            
            # For Gemini models, check if the container allows public access
            if is_gemini and not public:
                logger.warning("⚠️ Using Gemini with a clean URL requires the container to allow public access")
                logger.warning("⚠️ If the image doesn't display, your Azure container may need public read access")
                
            return clean_blob_url
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
                
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=azure_container_name,
                blob_name=object_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(seconds=expires_in)
            )
            
            # Return the full URL with SAS token
            return f"{blob_client.url}?{sas_token}"
    except Exception as e:
        logger.exception(f"Error generating Azure Blob Storage URL: {e}")
        return None

# --- Routes ---
@app.route('/')
def index():
    # Allow non-authenticated users to use the app with limited functionality
    is_logged_in = current_user.is_authenticated
    
    # Fetch conversations only if user is logged in
    conversations = []
    if is_logged_in:
        try:
            from models import Conversation
            conversations = Conversation.query.filter_by(
                is_active=True, 
                user_id=current_user.id
            ).order_by(Conversation.updated_at.desc()).all()
        except Exception as e:
            logger.error(f"Error fetching conversations: {e}")
    
    return render_template(
        'index.html', 
        user=current_user, 
        is_logged_in=is_logged_in,
        conversations=conversations
    )

@app.route('/login')
def login():
    # If user is already logged in, redirect to index
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Pass any flash messages to the template
    flash_messages = []
    if session.get('flash_messages'):
        flash_messages = session.pop('flash_messages')
    
    # Google OAuth is our exclusive login method
    return render_template('login.html', 
                          flash_messages=flash_messages,
                          oauth_enabled=True)
                          
@app.route('/privacy-policy')
def privacy_policy():
    """Privacy Policy page"""
    return render_template('privacy_policy.html')

@app.route('/terms-of-service')
def terms_of_service():
    """Terms of Service page"""
    return render_template('terms_of_service.html')

@app.route('/cookie-policy')
def cookie_policy():
    """Cookie Policy page"""
    return render_template('cookie_policy.html')
    
@app.route('/billing/account')
def redirect_billing():
    """
    Fallback handler for /billing/account redirections.
    Now that we have a real billing blueprint, redirect to the actual account management page.
    """
    # Log the redirection for monitoring
    logger.info(f"Redirecting from /billing/account to billing.account_management")
    
    # Redirect to the billing.account_management blueprint route
    return redirect(url_for('billing.account_management'))

@app.route('/test-upload')
@login_required
def test_upload_page():
    """
    A simple route to test the image upload functionality.
    This serves a static HTML page for testing without requiring the full UI.
    """
    return render_template('test_upload.html')

@app.route('/test-multimodal')
@login_required
def test_multimodal():
    """
    Debug route to test multimodal image handling.
    Tests the URL format compatibility with OpenRouter's multimodal API requirements.
    """
    try:
        # Create a test message with an image
        test_image_url = None
        
        # Try to get a test image URL from Azure Blob Storage
        if 'USE_AZURE_STORAGE' in globals() and USE_AZURE_STORAGE and 'container_client' in globals() and container_client:
            # List blobs to find an image
            for blob in container_client.list_blobs(max_results=5):
                if blob.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    test_image_url = get_object_storage_url(blob.name, public=False, expires_in=3600)
                    break
        
        # If no Azure image, use a sample image URL
        if not test_image_url:
            # Use a test image from the static folder
            test_image_url = url_for('static', filename='sample_image.jpg', _external=True)
        
        # Create a multimodal message in OpenRouter format
        multimodal_content = [
            {"type": "text", "text": "This is a test multimodal message with an image."},
            {"type": "image_url", "image_url": {"url": test_image_url}}
        ]
        
        result = {
            "success": True,
            "message": "Multimodal test message created",
            "image_url": test_image_url,
            "multimodal_content": multimodal_content,
            "is_valid_url": test_image_url.startswith(('http://', 'https://'))
        }
        
        # Return both JSON and rendered HTML
        if request.headers.get('Accept') == 'application/json':
            return jsonify(result)
        else:
            return render_template('test_multimodal.html', result=result)
    
    except Exception as e:
        error_msg = f"Error testing multimodal: {str(e)}"
        logger.exception(error_msg)
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"error": error_msg}), 500
        else:
            return f"<h1>Error</h1><p>{error_msg}</p>", 500

@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    """
    Route to handle image uploads for multimodal messages.
    Processes, resizes if needed, and stores images in Azure Blob Storage.
    
    The returned image URL will be included in the multimodal message content
    following OpenRouter's standardized format for all models:
    
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "User's message text"},
            {"type": "image_url", "image_url": {"url": "URL_RETURNED_FROM_THIS_ENDPOINT"}}
        ]
    }
    
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
                
                # Get original format and MIME type
                original_format = img.format
                original_mime_type = mimetypes.guess_type(filename)[0] or 'image/jpeg'
                
                # Check if format is WebP and convert to JPEG for better compatibility
                if original_format == 'WEBP' or extension.lower() == '.webp':
                    logger.info("Converting WebP image to JPEG for better model compatibility")
                    # If image has transparency (RGBA), convert to RGB
                    if img.mode == 'RGBA':
                        # Create a white background
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        # Paste the image on the background, using alpha channel as mask
                        background.paste(img, mask=img.split()[3])
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Use JPEG as the format
                    format_to_save = 'JPEG'
                    mime_type = 'image/jpeg'
                    # Update filename extension for storage
                    name_without_ext = os.path.splitext(unique_filename)[0]
                    unique_filename = f"{name_without_ext}.jpg"
                    logger.info(f"Converted WebP to JPEG: {unique_filename}")
                else:
                    # Use original format or fallback to JPEG
                    format_to_save = original_format or 'JPEG'
                    mime_type = original_mime_type
                
                # Save the processed image to memory stream
                img.save(processed_image_stream, format=format_to_save, quality=90)
                processed_image_stream.seek(0)
                logger.info(f"Processed image to dimensions: {img.width}x{img.height}, format: {format_to_save}")
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
                
                # Set content settings (MIME type)
                content_settings = ContentSettings(content_type=mime_type)
                
                # Upload the image data to Azure Blob Storage
                blob_client.upload_blob(
                    data=image_data,
                    content_settings=content_settings,
                    overwrite=True
                )
                
                # Check if a specific model is being used (from query params)
                target_model = request.args.get('model', None)
                
                # Generate a URL for the uploaded image
                # For Gemini models, use a clean URL without SAS token
                image_url = get_object_storage_url(
                    object_name=storage_path, 
                    public=False, 
                    expires_in=24*3600,
                    clean_url=False,  # Will be automatically set to True for Gemini models
                    model_name=target_model
                )
                
                # Log debugging information
                logger.info(f"Uploaded image to Azure Blob Storage with URL: {image_url[:50]}...")
                logger.info(f"Image MIME type: {mime_type}")
                logger.info(f"Target model (if specified): {target_model or 'None'}")
                
                # Add detailed compatibility warnings
                if '.webp' in storage_path.lower():
                    logger.warning("⚠️ WebP format detected - Gemini models may have issues with this format")
                    logger.warning("Consider using JPEG or PNG for better cross-model compatibility")
                
                parsed_url = urlparse(image_url) if image_url else None
                if parsed_url and parsed_url.query and target_model and "gemini" in target_model.lower():
                    logger.warning("⚠️ Gemini model detected with URL containing query parameters")
                    logger.warning("Gemini models typically reject URLs with SAS tokens or query parameters")
                    logger.warning("Try setting the container to allow public access for Gemini compatibility")
                    
                # Verify the URL is generated
                if not image_url:
                    logger.error("❌ Failed to generate URL for Azure Blob Storage")
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
@login_required
def get_conversations():
    """Get all conversations for the current user"""
    try:
        from models import Conversation
        
        # Log if this is a cache-busting request
        if request.args.get('_'):
            logger.info(f"Received cache-busting request for conversations at timestamp: {request.args.get('_')}")
        
        # Get all conversations for the current user, ordered by most recently updated first
        # Force a fresh query from the database (don't use cached results)
        db.session.expire_all()
        all_conversations = Conversation.query.filter_by(
            is_active=True, 
            user_id=current_user.id
        ).order_by(Conversation.updated_at.desc()).all()
        
        if not all_conversations:
            # Create a new conversation for this user if none exist
            title = "New Conversation"
            share_id = generate_share_id()
            conversation = Conversation(
                title=title, 
                share_id=share_id,
                user_id=current_user.id  # Associate conversation with user
            )
            db.session.add(conversation)
            try:
                db.session.commit()
                logger.info(f"Created initial conversation for user {current_user.id}")
                # Include created_at timestamp for proper date formatting in the UI
                conversations = [{"id": conversation.id, "title": conversation.title, "created_at": conversation.created_at.isoformat()}]
            except Exception as e:
                logger.exception(f"Error committing new conversation for user {current_user.id}: {e}")
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
        # Enhanced request logging for diagnosing 400 errors
        logger.info(f"chat: Request Content-Type: {request.content_type}")
        logger.info(f"chat: Request headers: {dict(request.headers)}")
        
        # Try different methods of getting JSON data
        data = None
        request_data = request.get_data(as_text=True)
        logger.info(f"chat: Raw request data: {request_data[:500]}...")  # Limit log size
        
        if request.is_json:
            data = request.get_json(silent=True)
            logger.info(f"chat: JSON data obtained: {data is not None}")
            if data:
                logger.info(f"chat: Data keys: {list(data.keys())}")
        else:
            logger.warning("chat: Request not identified as JSON")
            try:
                # Attempt to parse manually
                import json
                data = json.loads(request_data)
                logger.info(f"chat: Manually parsed JSON, keys: {list(data.keys())}")
            except json.JSONDecodeError as e:
                logger.error(f"chat: JSON parse error: {e}")
                
        if not data:
            logger.error("chat: Failed to extract JSON data from request")
            abort(400, description="Invalid request body. JSON expected.")

        # --- Get user input from structured 'messages' array (OpenAI-compatible format) ---
        frontend_messages = data.get('messages', [])
        user_message = ""
        image_url = None   # For backward compatibility
        image_urls = []    # Array of all image URLs
        
        if frontend_messages:
            # Process the latest user message to extract text and images
            latest_user_message = None
            for msg in reversed(frontend_messages):
                if msg.get('role') == 'user':
                    latest_user_message = msg
                    break
                    
            if latest_user_message:
                content = latest_user_message.get('content', [])
                
                # Handle both string content and array content formats
                if isinstance(content, str):
                    user_message = content
                    logger.info(f"Extracted text-only message from messages array: {user_message[:50]}...")
                elif isinstance(content, list):
                    # Extract text and images from the content array
                    for item in content:
                        if item.get('type') == 'text':
                            user_message = item.get('text', '')
                            logger.info(f"Extracted text from messages array: {user_message[:50]}...")
                        elif item.get('type') == 'image_url':
                            image_url_obj = item.get('image_url', {})
                            url = image_url_obj.get('url')
                            if url:
                                image_urls.append(url)
                                # Set image_url to the first image for backward compatibility
                                if not image_url:
                                    image_url = url
                                logger.info(f"Extracted image URL from messages array: {url[:50]}...")
        
        # Fallback to top-level fields if messages array wasn't processed successfully
        if not user_message:
            logger.warning("Using legacy top-level 'message' field as fallback")
            user_message = data.get('message', '')
            
        if not image_urls:
            # Get optional image URLs for multimodal messages (legacy format)
            legacy_image_url = data.get('image_url')
            legacy_image_urls = data.get('image_urls', [])
            
            if legacy_image_url:
                image_url = legacy_image_url
                image_urls.append(legacy_image_url)
                logger.warning(f"Using legacy top-level 'image_url' field as fallback: {image_url[:50]}...")
                
            if legacy_image_urls:
                for url in legacy_image_urls:
                    if url not in image_urls:  # Avoid duplicates
                        image_urls.append(url)
                logger.warning(f"Using legacy top-level 'image_urls' field as fallback")
        
        if image_urls:
            logger.info(f"Request contains {len(image_urls)} images")
        
        # Use .get for default model to avoid KeyError if '1' isn't present initially
        model_id = data.get('model', DEFAULT_PRESET_MODELS.get('1', 'google/gemini-flash-1.5')) 
        message_history = data.get('history', [])
        conversation_id = data.get('conversation_id', None)
        
        # For non-authenticated users, force the free model
        if not current_user.is_authenticated:
            is_free_model = False
            
            # First check: If the model ID contains the ':free' suffix
            if ':free' in model_id.lower():
                is_free_model = True
                logger.debug(f"Model {model_id} identified as free by suffix")
                
            # Second check: If the model is in our known free models list
            elif model_id in FREE_MODEL_FALLBACKS:
                is_free_model = True
                logger.debug(f"Model {model_id} identified as free from FREE_MODEL_FALLBACKS")
                
            # Third check: Check against OpenRouter's model info (if available)
            elif OPENROUTER_MODELS_INFO:
                # Look for this model in the OpenRouter data
                model_info = next((model for model in OPENROUTER_MODELS_INFO if model.get('id') == model_id), None)
                if model_info and model_info.get('is_free', False):
                    is_free_model = True
                    logger.debug(f"Model {model_id} identified as free from OpenRouter API data")

            # If it's not a free model, override with the default free model
            if not is_free_model:
                old_model = model_id  # Save for logging
                model_id = DEFAULT_PRESET_MODELS.get('6', 'google/gemini-2.0-flash-exp:free')
                logger.info(f"Non-authenticated user restricted to free model: {model_id} (was: {old_model})")

        from models import Conversation, Message # Ensure models are imported

        # --- Determine OpenRouter Model ID ---
        openrouter_model = OPENROUTER_MODELS.get(model_id, model_id) # Use .get fallback
        
        # --- Validate and ensure model is available in OpenRouter ---
        try:
            import model_validator
            
            # Check if the message contains images (for multimodal selection)
            has_image = image_url or (image_urls and len(image_urls) > 0)
            
            # Get the list of available models
            available_models = model_validator.get_available_models()
            
            # Check if the requested model is available
            if not model_validator.is_model_available(openrouter_model, available_models):
                logger.warning(f"Requested model {openrouter_model} is not available in OpenRouter")
                
                # Try to select a fallback model
                fallback_model = model_validator.get_fallback_model(
                    openrouter_model, 
                    SAFE_FALLBACK_MODELS,
                    available_models
                )
                
                if fallback_model:
                    logger.info(f"Using fallback model: {fallback_model} instead of {openrouter_model}")
                    openrouter_model = fallback_model
                else:
                    # If no fallback found, select model based on content type
                    adaptive_model = model_validator.select_multimodal_fallback(has_image, available_models)
                    logger.info(f"Using adaptive model selection: {adaptive_model}")
                    openrouter_model = adaptive_model
        except Exception as validation_error:
            logger.error(f"Error during model validation: {validation_error}")
            logger.error(traceback.format_exc())
            # Continue with the original model (we tried our best)

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
            # Associate conversation with the authenticated user
            if current_user and current_user.is_authenticated:
                conversation.user_id = current_user.id
                logger.info(f"Associating new conversation with user ID: {current_user.id}")
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

        # Extract text content from multimodal message if needed
        message_text = user_message
        
        # If message_history contains structured multimodal content, extract just the text
        if message_history and len(message_history) > 0:
            last_message = message_history[-1]
            if isinstance(last_message.get('content'), list):
                # Find the text component in the multimodal content
                for content_item in last_message.get('content', []):
                    if content_item.get('type') == 'text':
                        message_text = content_item.get('text', user_message)
                        logger.info(f"Extracted text content from multimodal message: {message_text[:50]}...")
                        break
                        
                # Also check for image_url in the multimodal content if not already provided
                if not image_url:
                    for content_item in last_message.get('content', []):
                        if content_item.get('type') == 'image_url' and content_item.get('image_url', {}).get('url'):
                            extracted_image_url = content_item.get('image_url', {}).get('url')
                            logger.info(f"Extracted image URL from multimodal message: {extracted_image_url[:50]}...")
                            image_url = extracted_image_url
                            break
        
        # Double check - if we still don't have an image_url, try to find it in the request JSON
        if not image_url and request.is_json:
            # Try to extract image_url directly from the JSON payload
            direct_image_url = request.json.get('image_url')
            if direct_image_url:
                image_url = direct_image_url
                logger.info(f"Found image_url directly in request JSON: {image_url[:50]}...")
        
        # Validate image URL if provided
        if image_url:
            if not image_url.startswith(('http://', 'https://')):
                logger.warning(f"Invalid image URL format: {image_url[:50]}... - must start with http:// or https://")
                # Don't use invalid URLs
                image_url = None
            else:
                logger.info(f"✅ Valid image URL format: {image_url[:50]}...")
        
        # Log what we're saving to the database
        logger.info(f"Saving user message to DB. Text: '{message_text[:50]}...' Image URL: {image_url[:50] if image_url else 'None'}")
        
        user_db_message = Message(
            conversation_id=conversation.id, 
            role='user', 
            content=message_text,  # Store the text component
            image_url=image_url    # Still store the image URL separately
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

        # First try to check if we have model info from the OpenRouter API
        model_supports_multimodal = False
        model_info_found = False
        
        # Method 1: Check model info from OpenRouter API data (most reliable)
        if OPENROUTER_MODELS_INFO and len(OPENROUTER_MODELS_INFO) > 0:
            # Look for this specific model in the cached OpenRouter API data
            for model_info in OPENROUTER_MODELS_INFO:
                if model_info.get('id', '').lower() == openrouter_model.lower():
                    # We found exact model info
                    model_info_found = True
                    # Use the is_multimodal flag from the API data if available
                    if 'is_multimodal' in model_info:
                        model_supports_multimodal = model_info.get('is_multimodal', False)
                        logger.info(f"✅ Found model in API data: {openrouter_model}, multimodal={model_supports_multimodal}")
                        break
        
        # Method 2: If we don't have API data for this model, use pattern matching as fallback
        if not model_info_found:
            logger.warning(f"No API info found for model {openrouter_model}, using pattern matching instead")
            for pattern in MULTIMODAL_MODELS:
                if pattern.lower() in openrouter_model.lower():
                    model_supports_multimodal = True
                    logger.info(f"✅ Detected multimodal support for model {openrouter_model} matching pattern {pattern}")
                    break
            
            # If we're sending an image but the model doesn't support it, log warning
            if image_url and not model_supports_multimodal:
                logger.warning(f"⚠️ Image URL provided but model {openrouter_model} doesn't seem to support multimodal input")
                logger.warning("⚠️ This may cause a 400 Bad Request error. Consider using a multimodal model instead.")

        # Load conversation history from database
        db_messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
        for msg in db_messages:
             if msg.id != user_db_message.id:
                 # Check if the message has an image URL and model supports multimodal
                 if msg.image_url and model_supports_multimodal:
                     # Format previous messages with images in multimodal format
                     multimodal_content = [
                         {"type": "text", "text": msg.content},
                         {"type": "image_url", "image_url": {"url": msg.image_url}}
                     ]
                     messages.append({'role': msg.role, 'content': multimodal_content})
                     logger.info(f"Including previous message with image in history: {msg.id}")
                 else:
                     # Standard text-only message
                     messages.append({'role': msg.role, 'content': msg.content})

        # Format the current user message - either standard text-only or multimodal
        # Following OpenRouter's unified multimodal format that works across all models:
        # https://openrouter.ai/docs#multimodal
                
        if (image_url or (image_urls and len(image_urls) > 0)) and model_supports_multimodal:
            # Create a multimodal content array with the text message
            multimodal_content = [
                {"type": "text", "text": user_message}
            ]
            
            # Process all images in the image_urls array
            urls_to_process = []
            if image_url:
                urls_to_process.append(image_url)
            if image_urls:
                urls_to_process.extend(image_urls)
                
            for url in urls_to_process:
                # Validate the image URL - ensure it's a publicly accessible URL
                if not url.startswith(('http://', 'https://')):
                    logger.error(f"❌ INVALID IMAGE URL: {url[:100]}...")
                    logger.error("Image URL must start with http:// or https://. Skipping this image.")
                    continue
                
                # Check if this is an Azure Blob Storage URL that needs to be optimized for the model
                is_azure_url = 'blob.core.windows.net' in url
                processed_url = url
                
                # If using Azure Storage and this is a Gemini model, we might need to regenerate
                # a "clean" URL without SAS tokens that Gemini can process better.
                if is_azure_url and "gemini" in openrouter_model.lower():
                    try:
                        # Extract the blob name from the URL
                        blob_name = url.split('?')[0].split('/')[-1]
                        logger.info(f"Extracted blob name: {blob_name}")
                        
                        # Regenerate a clean URL for Gemini
                        processed_url = get_object_storage_url(
                            blob_name, 
                            public=False, 
                            expires_in=3600, 
                            clean_url=True,
                            model_name="gemini"
                        )
                        logger.info(f"Regenerated clean URL for Gemini: {processed_url[:50]}...")
                    except Exception as url_error:
                        logger.error(f"Error regenerating clean URL: {url_error}")
                        # Continue with original URL if regeneration fails
                
                # Log detailed image information
                try:
                    # Parse URL components
                    parsed_url = urlparse(processed_url)
                    
                    # Check for query parameters that might indicate a SAS token
                    has_query_params = bool(parsed_url.query)
                    domain = parsed_url.netloc
                    path = parsed_url.path
                    extension = os.path.splitext(path)[1].lower()
                    
                    logger.info(f"📷 MULTIMODAL IMAGE {len(multimodal_content)} DETAILS:")
                    logger.info(f"  Domain: {domain}")
                    logger.info(f"  Path: {path}")
                    logger.info(f"  File Extension: {extension or 'none'}")
                    logger.info(f"  Has Query Parameters: {has_query_params}")
                    logger.info(f"  Model: {openrouter_model}")
                    
                    # Check for potential issues
                    if not extension:
                        logger.warning("⚠️ Image URL has no file extension - may cause issues with some models")
                    
                    if extension not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        logger.warning(f"⚠️ Unusual file extension: {extension} - may not be supported by all models")
                    
                    if has_query_params:
                        logger.warning("⚠️ URL contains query parameters (possibly SAS token) - may cause issues with some models")
                    
                    if 'blob.core.windows.net' in domain and has_query_params and "gemini" in openrouter_model.lower():
                        logger.warning("⚠️ Gemini model with Azure Blob Storage URL + SAS token - high probability of failure")
                        logger.warning("⚠️ Consider setting your Azure Blob Storage container to allow public access")
                    
                    # Check if URL has unusual characters
                    if any(c in processed_url for c in ['&', '+', '%', ' ']):
                        logger.warning("⚠️ URL contains special characters - may cause issues with some models")
                except Exception as url_parse_error:
                    logger.error(f"Error analyzing image URL: {url_parse_error}")
                
                # Add this image to the multimodal content
                multimodal_content.append({
                    "type": "image_url", 
                    "image_url": {"url": processed_url}
                })
            
            # Add the multimodal content to messages if we have at least one valid image
            if len(multimodal_content) > 1:  # First item is text, so we need more than 1 item
                messages.append({'role': 'user', 'content': multimodal_content})
                logger.info(f"✅ Added multimodal message with {len(multimodal_content) - 1} images to {openrouter_model}")
                
                # Model-specific guidance for multiple images
                if "gemini" in openrouter_model.lower():
                    logger.info("ℹ️ Using Gemini model - ensure image URLs are simple and publicly accessible")
                    logger.info("ℹ️ Gemini often rejects complex URLs with tokens or special parameters")
                    logger.info("ℹ️ Gemini models can process up to 16 images, but work best with 1-4 images")
                    
                    # Additional check for WebP format with Gemini
                    if any(os.path.splitext(urlparse(url).path)[1].lower() == '.webp' for url in urls_to_process if url.startswith(('http://', 'https://'))):
                        logger.warning("⚠️ WebP format(s) with Gemini model - high probability of failure")
                        logger.warning("⚠️ Consider converting WebP images to JPEG or PNG for Gemini compatibility")
                
                elif "claude" in openrouter_model.lower():
                    logger.info("ℹ️ Using Claude model - handles most image formats but prefers standard URLs")
                    # Claude 3 Opus/Sonnet supports up to 5 images, but check the limits for your specific model
                    if len(multimodal_content) > 6:  # 1 text + 5 images
                        logger.warning("⚠️ Claude model - more than 5 images may not be fully processed")
                
                elif "gpt-4" in openrouter_model.lower():
                    logger.info("ℹ️ Using GPT-4 model - generally most flexible with image URLs")
                    # GPT-4 Vision (gpt-4-vision-preview) can handle up to 20 images
                    if len(multimodal_content) > 21:  # 1 text + 20 images
                        logger.warning("⚠️ GPT-4 Vision - more than 20 images may not be fully processed")
                
                # Log full payload for debugging multimodal messages
                try:
                    logger.debug(f"Multimodal message payload: {json.dumps(multimodal_content, indent=2)}")
                except Exception as e:
                    logger.debug(f"Could not serialize multimodal content for logging: {e}")
            else:
                # No valid images were found, fall back to text-only
                logger.warning("⚠️ No valid image URLs found. Falling back to text-only message.")
                messages.append({'role': 'user', 'content': user_message})
        else:
            # Standard text-only message
            messages.append({'role': 'user', 'content': user_message})
        
        # Log if image was provided but model doesn't support it
        if (image_url or (image_urls and len(image_urls) > 0)) and not model_supports_multimodal:
            logger.warning(f"⚠️ Image URL(s) provided but model {openrouter_model} doesn't support multimodal input. Images ignored.")

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
        # Before creating payload, ensure we have correct content format for each model type
        # OpenRouter expects different message content formats for multimodal vs non-multimodal models
        
        # Check if model supports multimodal content
        model_supports_multimodal = False
        for pattern in MULTIMODAL_MODELS:
            if pattern.lower() in openrouter_model.lower():
                model_supports_multimodal = True
                logger.info(f"Model {openrouter_model} supports multimodal content matching pattern {pattern}")
                break
        
        # Transform messages if needed to match model capabilities
        processed_messages = []
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            
            # Only user and assistant messages need content format adaptation
            if role in ['user', 'assistant']:
                # Handle array content for multimodal messages
                if isinstance(content, list):
                    if model_supports_multimodal:
                        # Keep multimodal format for models that support it
                        processed_messages.append(msg)
                        logger.info(f"Keeping multimodal content format for {role} message with model {openrouter_model}")
                    else:
                        # For non-multimodal models, extract just the text content
                        text_content = None
                        for item in content:
                            if item.get('type') == 'text':
                                text_content = item.get('text', '')
                                break
                        
                        if text_content:
                            # Create a text-only message
                            processed_messages.append({
                                'role': role,
                                'content': text_content  # Plain string content
                            })
                            logger.info(f"Converted multimodal content to text-only for {role} message with non-multimodal model {openrouter_model}")
                        else:
                            # Fallback if no text content found
                            logger.warning(f"No text content found in multimodal message, using empty string")
                            processed_messages.append({
                                'role': role,
                                'content': ""
                            })
                else:
                    # Regular text message, no conversion needed
                    processed_messages.append(msg)
            else:
                # System messages and others pass through unchanged
                processed_messages.append(msg)
        
        # Log the transformation summary
        logger.info(f"Message format adaptation: {len(messages)} original messages → {len(processed_messages)} processed messages")
        if len(messages) != len(processed_messages):
            logger.warning(f"Message count changed during format adaptation! Original: {len(messages)}, Processed: {len(processed_messages)}")
        
        # Create payload with the processed messages
        payload = {
            'model': openrouter_model,
            'messages': processed_messages,
            'stream': True,
            'include_reasoning': True  # Enable reasoning tokens for all models that support it
        }
        
        # Note: We don't need to add image_url separately as it's now included in the messages content
        # for multimodal models when an image is provided
        
        logger.info(f"Payload prepared for OpenRouter with model: {openrouter_model}, multimodal support: {model_supports_multimodal}")
        
        # --- ADD DETAILED LOGGING FOR TROUBLESHOOTING MULTIMODAL IMAGES ---
        try:
            # Check if there's a multimodal message in the processed_messages that will be sent to OpenRouter
            has_multimodal_message = False
            for msg in payload['messages']:  # Important: check the processed_messages in the payload!
                if isinstance(msg.get('content'), list):
                    has_multimodal_message = True
                    # Log the structure of the multimodal message
                    logger.info("Found multimodal message in FINAL payload:")
                    for i, content_item in enumerate(msg.get('content', [])):
                        item_type = content_item.get('type', 'unknown')
                        if item_type == 'text':
                            logger.info(f"  Content item {i}: type=text, text={content_item.get('text', '')[:50]}...")
                        elif item_type == 'image_url':
                            image_url_obj = content_item.get('image_url', {})
                            url = image_url_obj.get('url', 'none')
                            
                            # Double-check URL format - must be a valid public URL for OpenRouter
                            is_valid_url = url.startswith(('http://', 'https://'))
                            if not is_valid_url:
                                logger.error(f"❌ INVALID URL FORMAT DETECTED in payload: {url[:50]}...")
                                logger.error("This will cause the image to be ignored by the model.")
                            else:
                                logger.info(f"  Content item {i}: type=image_url, url={url[:50]}...")
            
            # Now compare what was in the original vs what's in the processed payload
            original_has_multimodal = any(isinstance(msg.get('content'), list) for msg in messages)
            if original_has_multimodal != has_multimodal_message:
                if original_has_multimodal and not has_multimodal_message:
                    logger.info("✅ Successfully converted multimodal content to text-only for non-multimodal model")
                elif not original_has_multimodal and has_multimodal_message:
                    logger.warning("⚠️ Unexpected conversion: text-only content became multimodal!")
            
            if image_url and not has_multimodal_message:
                logger.info("ℹ️ image_url was provided but no multimodal message in final payload - correctly converted for non-multimodal model")
            
            # Check final model and multimodal status match
            selected_model = payload.get('model', '')
            model_supports_multimodal = False
            for indicator in MULTIMODAL_MODELS:
                if indicator.lower() in selected_model.lower():
                    model_supports_multimodal = True
                    break
            
            # Verify content format matches model capabilities
            if model_supports_multimodal != has_multimodal_message:
                if model_supports_multimodal and not has_multimodal_message:
                    logger.warning("⚠️ Model supports multimodal content but we're sending text-only!")
                elif not model_supports_multimodal and has_multimodal_message:
                    logger.warning("⚠️ Model does NOT support multimodal but we're still sending multimodal content!")
            else:
                logger.info(f"✅ Content format correctly matched to model capabilities: multimodal={model_supports_multimodal}")
            
            # Create a safe copy of the payload for logging (to avoid credentials leaks)
            log_payload = payload.copy()
            # Use json.dumps for clean logging of the entire payload
            final_payload_json = json.dumps(log_payload, indent=2)
            logger.debug(f"PAYLOAD DEBUG: Final payload being sent to OpenRouter:\n{final_payload_json}")
        except Exception as json_err:
            logger.error(f"PAYLOAD DEBUG: Error serializing payload for logging: {json_err}")
        # --- END OF ADDED LOGGING ---
        
        logger.debug(f"Sending request to OpenRouter with model: {openrouter_model}. History length: {len(messages)}, include_reasoning: True")

        # --- Define the SYNC Generator using requests ---
        def generate():
            # Import json module inside the function scope to avoid NameError
            import json
            
            assistant_response_content = [] 
            final_prompt_tokens = None
            final_completion_tokens = None
            final_model_id_used = None
            assistant_message_id = None 
            current_conv_id = conversation.id 
            requested_model_id = model_id 
            
            # --- Verify user has sufficient credits if authenticated ---
            if current_user and current_user.is_authenticated:
                try:
                    from billing import check_sufficient_credits, calculate_openrouter_credits
                    
                    # Estimate token usage based on input size
                    # Rough estimation: 1 token = ~4 characters for English text
                    estimated_prompt_tokens = sum(len(msg.get('content', '')) // 4 + 10 for msg in messages)
                    # Assume completion will be around half the prompt length
                    estimated_completion_tokens = max(100, estimated_prompt_tokens // 2)
                    
                    # We'll use the model ID directly with the dynamic pricing system
                    
                    # Calculate estimated credits
                    estimated_credits = calculate_openrouter_credits(
                        prompt_tokens=estimated_prompt_tokens,
                        completion_tokens=estimated_completion_tokens,
                        model_id=model_id
                    )
                    
                    # Check if user has sufficient credits
                    has_credits = check_sufficient_credits(current_user.id, estimated_credits)
                    
                    # If not, return an error
                    if not has_credits:
                        logger.warning(f"User {current_user.id} has insufficient credits for request")
                        yield f"data: {json.dumps({'type': 'error', 'error': 'Insufficient credits. Please purchase more credits to continue using premium models.'})}\n\n"
                        return
                        
                    logger.info(f"User {current_user.id} has sufficient credits for request (est. {estimated_credits} credits)")
                    
                except Exception as credit_error:
                    logger.error(f"Error checking credits: {credit_error}")
                    # Continue even if credit check fails (don't block the request)
            
            try:
                # First verify the payload is valid and contains all required fields
                if not payload.get('model'):
                    error_message = "Invalid payload: 'model' field is missing"
                    logger.error(error_message)
                    yield f"data: {json.dumps({'type': 'error', 'error': error_message})}\n\n"
                    return
                
                if not payload.get('messages') or len(payload.get('messages', [])) == 0:
                    error_message = "Invalid payload: 'messages' field is empty or missing"
                    logger.error(error_message)
                    yield f"data: {json.dumps({'type': 'error', 'error': error_message})}\n\n"
                    return
                
                # Check for any multimodal content issues before sending
                has_multimodal_content = False
                for msg in payload.get('messages', []):
                    content = msg.get('content')
                    if isinstance(content, list):
                        has_multimodal_content = True
                        # Check for common multimodal content issues
                        for item in content:
                            if item.get('type') == 'image_url':
                                image_url_obj = item.get('image_url', {})
                                url = image_url_obj.get('url', '')
                                if not url or not isinstance(url, str) or not url.startswith(('http://', 'https://')):
                                    error_message = f"Invalid image URL in multimodal content: {url[:100]}"
                                    logger.error(error_message)
                                    yield f"data: {json.dumps({'type': 'error', 'error': error_message})}\n\n"
                                    return
                
                # Log multimodal content status for extra clarity
                if has_multimodal_content:
                    logger.info(f"Detected multimodal content in the final payload sent to {payload.get('model')}")
                
                # Now make the actual API request with better error handling
                try:
                    logger.info(f"Making API request to OpenRouter with model {payload.get('model')}")
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
                        # Attempt to parse the error response for more details
                        try:
                            error_json = response.json()
                            error_detail = error_json.get('error', {}).get('message', '')
                            if error_detail:
                                error_text = f"{error_text} - Detail: {error_detail}"
                        except:
                            # If we can't parse JSON, just use the raw text
                            pass
                            
                        # For 400 errors, add more helpful diagnostics based on common issues
                        if response.status_code == 400:
                            if has_multimodal_content:
                                error_text += " (Possible cause: Invalid multimodal content format or unsupported images)"
                                # Check if we already logged specific model warnings
                                if "gemini" in payload.get('model', '').lower():
                                    error_text += " - Note: Gemini models are particularly strict about image formats and URLs"
                                
                            error_text += " - Please check the model supports the content type you're sending."
                        
                        logger.error(f"OpenRouter API error: {response.status_code} - {error_text}")
                        yield f"data: {json.dumps({'type': 'error', 'error': f'API Error: {response.status_code} - {error_text}'})}\n\n"
                        return # Stop generation
                        
                except requests.RequestException as req_err:
                    error_message = f"Request failed: {req_err}"
                    logger.error(error_message)
                    yield f"data: {json.dumps({'type': 'error', 'error': error_message})}\n\n"
                    return

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
                        
                        # --- Record usage for billing ---
                        if current_user and current_user.is_authenticated and final_prompt_tokens and final_completion_tokens:
                            try:
                                from billing import record_usage, calculate_openrouter_credits
                                
                                # Get the model ID that was actually used
                                model_name = final_model_id_used or requested_model_id
                                
                                # Calculate credits used
                                credits_used = calculate_openrouter_credits(
                                    prompt_tokens=final_prompt_tokens,
                                    completion_tokens=final_completion_tokens,
                                    model_id=model_name
                                )
                                
                                # Record usage
                                record_usage(
                                    user_id=current_user.id,
                                    credits_used=credits_used,
                                    usage_type="chat",
                                    model_id=model_name,
                                    message_id=assistant_message_id,
                                    prompt_tokens=final_prompt_tokens,
                                    completion_tokens=final_completion_tokens
                                )
                                
                                logger.info(f"Recorded usage: {credits_used} credits for message {assistant_message_id}")
                            except Exception as billing_error:
                                logger.error(f"Error recording billing usage: {billing_error}")
                                # Don't fail the whole request if billing recording fails

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
# Helper function to fetch models from OpenRouter
def _fetch_openrouter_models():
    """Fetch models from OpenRouter API"""
    try:
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            logger.error("OPENROUTER_API_KEY not found")
            return None

        headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}

        logger.debug("Fetching models from OpenRouter...")
        response = requests.get(
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
        
        # Update the cache
        OPENROUTER_MODELS_CACHE["data"] = result_data
        OPENROUTER_MODELS_CACHE["timestamp"] = time.time()
        
        # Also update OPENROUTER_MODELS_INFO for the non-authenticated user check
        global OPENROUTER_MODELS_INFO
        OPENROUTER_MODELS_INFO = processed_models
        
        logger.info(f"Fetched and cached {len(processed_models)} models from OpenRouter")
        
        return result_data
    except Exception as e:
        logger.exception("Error fetching models from OpenRouter")
        return None

@app.route('/api/get_model_prices', methods=['GET'])
def get_model_prices():
    """ 
    Get the current model prices from the database
    This is an updated implementation that uses the database as the primary source
    """
    try:
        # First try to get the model prices from the database
        from models import OpenRouterModel
        
        # Query all models from the database
        db_models = OpenRouterModel.query.all()
        
        if db_models:
            # Convert database models to the expected format
            prices = {}
            for db_model in db_models:
                prices[db_model.model_id] = {
                    'input_price': db_model.input_price_usd_million,
                    'output_price': db_model.output_price_usd_million,
                    'context_length': db_model.context_length,
                    'is_multimodal': db_model.is_multimodal,
                    'model_name': db_model.name,
                    'cost_band': db_model.cost_band,
                    'source': 'database'
                }
            
            # Use the timestamp of the most recently updated model
            latest_model = OpenRouterModel.query.order_by(OpenRouterModel.last_fetched_at.desc()).first()
            last_updated = latest_model.last_fetched_at.isoformat() if latest_model else None
            
            logger.info(f"Retrieved prices for {len(prices)} models from database")
            
            # Return the model prices from the database
            return jsonify({
                'success': True,
                'prices': prices,
                'last_updated': last_updated
            })
            
        else:
            # If no models in the database, try to fetch them
            logger.warning("No models found in database, fetching from API...")
            success = fetch_and_store_openrouter_prices()
            
            if success:
                # Check if models were added to the database
                db_models = OpenRouterModel.query.all()
                if db_models:
                    # Call this function again to return the database results
                    return get_model_prices()
            
            # If no models in database and fetch failed, fall back to the old cache
            logger.warning("Database is still empty, falling back to cache...")
            prices = model_prices_cache.get('prices', {})
            
            # If cache is also empty, try to fetch directly (old method)
            if not prices:
                logger.warning("Cache is also empty, attempting direct API fetch...")
                success = fetch_and_store_openrouter_prices()
                prices = model_prices_cache.get('prices', {})
            
            # If still no prices, use the fallback data as a last resort
            if not prices:
                logger.warning("All data sources failed, using fallback data...")
                prices = _generate_fallback_model_data()
            
            # Ensure all models have cost bands
            for model_id, model_data in prices.items():
                if 'cost_band' not in model_data:
                    # Calculate the cost band if not present
                    input_price = model_data.get('input_price', 0) or 0
                    output_price = model_data.get('output_price', 0) or 0
                    max_cost = max(input_price, output_price)
                    
                    if max_cost >= 100.0:
                        cost_band = '$$$$'
                    elif max_cost >= 10.0:
                        cost_band = '$$$'
                    elif max_cost >= 1.0:
                        cost_band = '$$'
                    elif max_cost >= 0.01:
                        cost_band = '$'
                    else:
                        cost_band = '' # Free
                        
                    model_data['cost_band'] = cost_band
            
            # Return the modified prices dictionary and the last_updated timestamp
            return jsonify({
                'success': True,
                'prices': prices,
                'last_updated': model_prices_cache.get('last_updated')
            })
            
    except Exception as e:
        logger.exception(f"Error getting model prices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _generate_fallback_model_data():
    """
    Generate fallback model data when OpenRouter API is unavailable.
    This ensures the frontend can still function with essential models.
    """
    # Get current timestamp for the fallback data
    current_time = datetime.now().isoformat()
    
    # Define fallback models with their properties
    fallback_models = {
        # GPT-4 Series
        'openai/gpt-4o': {
            'input_price': 10.0,
            'output_price': 30.0,
            'raw_input_price': 5.0,
            'raw_output_price': 15.0,
            'context_length': 128000,
            'is_multimodal': True,
            'model_name': 'GPT-4o',
            'is_reasoning': True,
            'cost_band': '$$$'
        },
        'openai/o4-Mini-High': {
            'input_price': 2.0,
            'output_price': 6.0,
            'raw_input_price': 1.0,
            'raw_output_price': 3.0,
            'context_length': 128000,
            'is_multimodal': False,
            'model_name': 'GPT-4o Mini High',
            'is_reasoning': True,
            'cost_band': '$$'
        },
        # Claude Models
        'anthropic/claude-3.7-sonnet': {
            'input_price': 15.0,
            'output_price': 60.0,
            'raw_input_price': 7.5,
            'raw_output_price': 30.0,
            'context_length': 200000,
            'is_multimodal': False,
            'model_name': 'Claude 3.7 Sonnet',
            'is_reasoning': True,
            'cost_band': '$$$$'
        },
        'anthropic/claude-3.5-sonnet': {
            'input_price': 3.0,
            'output_price': 15.0,
            'raw_input_price': 1.5,
            'raw_output_price': 7.5,
            'context_length': 200000,
            'is_multimodal': True,
            'model_name': 'Claude 3.5 Sonnet Vision',
            'is_reasoning': True,
            'cost_band': '$$$'
        },
        # Gemini Models
        'google/gemini-2.5-pro-preview-03-25': {
            'input_price': 14.0,
            'output_price': 42.0,
            'raw_input_price': 7.0,
            'raw_output_price': 21.0,
            'context_length': 100000,
            'is_multimodal': True,
            'model_name': 'Gemini 2.5 Pro Preview',
            'is_reasoning': True,
            'cost_band': '$$$$'
        },
        # Perplexity Models
        'perplexity/sonar-pro': {
            'input_price': 1.0,
            'output_price': 6.0,
            'raw_input_price': 0.5,
            'raw_output_price': 3.0,
            'context_length': 24000,
            'is_multimodal': False,
            'model_name': 'Perplexity Sonar Pro',
            'is_perplexity': True,
            'cost_band': '$$'
        },
        # Free Models
        'google/gemini-2.0-flash-exp:free': {
            'input_price': 0.0,
            'output_price': 0.0,
            'raw_input_price': 0.0,
            'raw_output_price': 0.0,
            'context_length': 8000,
            'is_multimodal': False,
            'model_name': 'Gemini 2.0 Flash (FREE)',
            'is_free': True,
            'cost_band': ''  # Empty cost band for free models
        }
    }
    
    # Model properties are now directly usable by frontend filtering
    # Log that we're using fallback data
    logger.warning(f"Using fallback data for {len(fallback_models)} essential models")
    
    # Also update OPENROUTER_MODELS_INFO for the non-authenticated user check
    # Create a list of model info objects in the expected format
    global OPENROUTER_MODELS_INFO
    OPENROUTER_MODELS_INFO = []
    
    for model_id, model_data in fallback_models.items():
        # Convert the fallback data format to match what would come from the API
        model_info = {
            'id': model_id,
            'name': model_data.get('model_name', ''),
            'description': '',
            'pricing': {
                'prompt': str(model_data.get('raw_input_price', 0) / 1000000),  # Convert back to per-token price
                'completion': str(model_data.get('raw_output_price', 0) / 1000000)  # Convert back to per-token price
            },
            'context_length': model_data.get('context_length', 0),
            'is_free': model_data.get('is_free', False),
            'is_multimodal': model_data.get('is_multimodal', False)
        }
        OPENROUTER_MODELS_INFO.append(model_info)
    
    logger.info(f"Updated OPENROUTER_MODELS_INFO with {len(OPENROUTER_MODELS_INFO)} fallback models")
    
    return fallback_models

@app.route('/api/refresh_model_prices', methods=['POST'])
def refresh_model_prices():
    """ Manually refresh model prices from OpenRouter API """
    try:
        # Call the function to fetch and store prices
        success = fetch_and_store_openrouter_prices()
        
        if success:
            return jsonify({
                'success': True,
                'prices': model_prices_cache['prices'],
                'last_updated': model_prices_cache['last_updated'],
                'message': 'Model prices refreshed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to refresh model prices from OpenRouter API'
            }), 500
            
    except Exception as e:
        logger.error(f"Error refreshing model prices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/model-pricing', methods=['GET'])
def get_model_pricing():
    """ Fetch model pricing information """
    try:
        from price_updater import fetch_and_store_openrouter_prices, model_prices_cache
        
        # If cache is empty, fetch prices from OpenRouter
        if not model_prices_cache['prices']:
            logger.info("Model prices cache is empty, fetching from OpenRouter API...")
            success = fetch_and_store_openrouter_prices()
            
            if not success:
                logger.error("Failed to fetch prices from OpenRouter API")
                return jsonify({
                    "error": "Unable to connect to OpenRouter API",
                    "message": "Please try again later or contact support if the problem persists.",
                    "data": []
                }), 200  # Return 200 so the error can be handled gracefully in the UI
        
        # Process models to create pricing data
        pricing_data = []
        
        # Define our internal price mapping (multiply OpenRouter prices by markup factor)
        markup_factor = 2.0
        
        # Fallback for throughput estimates based on model type
        def get_throughput_estimate(model_id):
            if "gpt-3.5" in model_id.lower() or "llama" in model_id.lower():
                return "High (~500 tokens/sec)"
            elif "gpt-4" in model_id.lower() or ("claude-3" in model_id.lower() and "opus" in model_id.lower()):
                return "Limited (~50 tokens/sec)"
            else:
                return "No data"
        
        # Process the models to extract pricing information
        for model_id, model_data in model_prices_cache['prices'].items():
            # Get model name (format from ID if not available)
            model_name = model_id.split('/')[-1].replace('-', ' ').title()
            is_autorouter = "router" in model_id.lower() or "openrouter" in model_id.lower()
            
            # Extract pricing information
            input_price_per_token = model_data['input_price'] / 1000000  # Convert from per million tokens
            output_price_per_token = model_data['output_price'] / 1000000  # Convert from per million tokens
            
            # Handle free models
            is_free_model = (input_price_per_token == 0 and output_price_per_token == 0)
            
            # Apply markup to prices
            our_input_price = float(input_price_per_token) * markup_factor if input_price_per_token else 0
            our_output_price = float(output_price_per_token) * markup_factor if output_price_per_token else 0
            
            # Format prices for display (per million tokens)
            if is_autorouter:
                # For AutoRouter, we display "Variable" but use a nominal value for sorting
                input_price_display = "Variable"
                output_price_display = "Variable"
            elif is_free_model or our_input_price == 0:
                # For free models, explicitly show $0.00
                input_price_display = "$0.00"
                output_price_display = "$0.00" if our_output_price == 0 else f"${our_output_price * 1000000:.2f}"
            else:
                # Standard pricing display for most models
                input_price_display = f"${our_input_price * 1000000:.2f}"
                output_price_display = f"${our_output_price * 1000000:.2f}" if our_output_price else "$0.00"
            
            # Get context length and multimodal support
            context_length = model_data.get('context_length', 'N/A')
            is_multimodal = model_data.get('is_multimodal', False)
            
            # Get throughput estimate
            throughput_estimate = get_throughput_estimate(model_id)
            
            pricing_data.append({
                "model_id": model_id,
                "model_name": model_name,
                "input_price": input_price_display,
                "output_price": output_price_display,
                "context_length": context_length,
                "throughput": throughput_estimate,
                "multimodal": "Yes" if is_multimodal else "No"
            })
        
        # Add the manually defined text-embedding-3-large model
        pricing_data.append({
            "model_id": "text-embedding-3-large",
            "model_name": "Text Embedding 3 Large",
            "input_price": "$2.00",  # $1 per million with markup
            "output_price": "$0.00",  # Changed from "N/A" to "$0.00" for consistency
            "context_length": "8192",
            "throughput": "Very High",
            "multimodal": "No"
        })
        
        # Sort models alphabetically for consistent display
        pricing_data.sort(key=lambda x: x['model_name'].lower())
        
        return jsonify({
            "data": pricing_data, 
            "last_updated": model_prices_cache['last_updated']
        })
            
    except Exception as e:
        logger.exception(f"Error processing model pricing data: {e}")
        return jsonify({
            "error": "Server error processing model pricing data",
            "message": "We encountered an issue retrieving pricing information. Please try again later.",
            "data": []
        }), 200  # Return 200 so frontend can handle gracefully

@app.route('/models', methods=['GET'])
def get_models():
    """ 
    Fetch available models from the database
    This is an updated implementation that uses the database as the primary source
    """
    try:
        from models import OpenRouterModel
        
        # Query all models from the database
        db_models = OpenRouterModel.query.order_by(OpenRouterModel.name).all()
        
        if db_models:
            # Convert SQLAlchemy models to the format expected by the frontend
            processed_models = []
            for db_model in db_models:
                # Create a model data dict in the format expected by the frontend
                model_data = {
                    'id': db_model.model_id,
                    'name': db_model.name,
                    'description': db_model.description or '',
                    'context_length': db_model.context_length,
                    'pricing': {
                        # Convert back to per-token pricing from per-million
                        'prompt': str(db_model.input_price_usd_million / 1000000),
                        'completion': str(db_model.output_price_usd_million / 1000000)
                    },
                    'is_multimodal': db_model.is_multimodal,
                    'is_free': db_model.input_price_usd_million == 0 and db_model.output_price_usd_million == 0,
                    'is_perplexity': 'perplexity/' in db_model.model_id.lower(),
                    'is_reasoning': any(keyword in db_model.model_id.lower() or 
                                       (db_model.name and keyword in db_model.name.lower()) or 
                                       (db_model.description and keyword in db_model.description.lower())
                                       for keyword in ['reasoning', 'opus', 'o1', 'o3'])
                }
                processed_models.append(model_data)
                
            # Create the response in the same format as the original API
            result_data = {"data": processed_models}
            
            # For backward compatibility, still update the cache
            if 'OPENROUTER_MODELS_CACHE' in globals():
                OPENROUTER_MODELS_CACHE["data"] = result_data
                OPENROUTER_MODELS_CACHE["timestamp"] = time.time()
                
            if 'OPENROUTER_MODELS_INFO' in globals():
                OPENROUTER_MODELS_INFO = processed_models
                
            logger.info(f"Retrieved {len(processed_models)} models from database")
            return jsonify(result_data)
            
        else:
            # If no models in database, trigger a fetch from the API
            logger.warning("No models found in database, fetching from API...")
            from price_updater import fetch_and_store_openrouter_prices
            success = fetch_and_store_openrouter_prices()
            
            if success:
                # Try to fetch from database again
                db_models = OpenRouterModel.query.order_by(OpenRouterModel.name).all()
                if db_models:
                    logger.info(f"Successfully fetched and stored {len(db_models)} models")
                    # Recursively call this function to format and return the results
                    return get_models()
            
            # If database is still empty after fetching, fall back to the old cache/API method
            logger.warning("Database is still empty after fetch attempt, falling back to old method")
            
            # Check cache first
            if 'OPENROUTER_MODELS_CACHE' in globals() and OPENROUTER_MODELS_CACHE["data"] is not None:
                logger.info("Using cached models as database fallback")
                return jsonify(OPENROUTER_MODELS_CACHE["data"])
                
            # Last resort: try direct API fetch (old method)
            logger.info("Attempting direct API fetch as final fallback")
            result_data = _fetch_openrouter_models()
            if result_data:
                return jsonify(result_data)
            
            # If all else failed
            logger.error("All methods failed to retrieve model data")
            return jsonify({
                "error": "Failed to retrieve models",
                "message": "We're experiencing temporary issues. Please try again in a few minutes."
            }), 200  # Using 200 so frontend can handle gracefully

    except Exception as e:
        logger.exception(f"Error in get_models: {e}")
        
        # Try to return cached data if available during exception
        if 'OPENROUTER_MODELS_CACHE' in globals() and OPENROUTER_MODELS_CACHE.get("data") is not None:
            logger.info("Using cached data during exception handling")
            return jsonify(OPENROUTER_MODELS_CACHE["data"])
            
        # If all else fails, return a friendly error
        return jsonify({
            "error": "Failed to retrieve models",
            "message": "Please try refreshing the page or contact support if the problem persists."
        }), 200  # Using 200 so frontend can handle gracefully


@app.route('/save_preference', methods=['POST'])
def save_preference():
    """ Save user model preference """
    try:
        # Enhanced request logging
        logger.info(f"save_preference: Request Content-Type: {request.content_type}")
        logger.info(f"save_preference: Request headers: {dict(request.headers)}")
        
        # Try different methods of getting JSON data
        data = None
        request_data = request.get_data(as_text=True)
        logger.info(f"save_preference: Raw request data: {request_data}")
        
        if request.is_json:
            data = request.get_json(silent=True)
            logger.info(f"save_preference: JSON data from request.get_json(): {data}")
        else:
            logger.warning("save_preference: Request not identified as JSON")
            try:
                # Attempt to parse manually
                import json
                data = json.loads(request_data)
                logger.info(f"save_preference: Manually parsed JSON: {data}")
            except json.JSONDecodeError as e:
                logger.error(f"save_preference: JSON parse error: {e}")
        
        if not data: abort(400, description="Invalid request body. JSON expected.")
        
        preset_id = data.get('preset_id')
        model_id = data.get('model_id')
        logger.info(f"save_preference: Extracted preset_id: {preset_id}, model_id: {model_id}")
        
        if not preset_id or not model_id: abort(400, description="Missing preset_id or model_id")
        try:
            preset_id = int(preset_id)
            if not 1 <= preset_id <= 6: abort(400, description="preset_id must be between 1 and 6")
        except ValueError: 
            logger.error(f"save_preference: Invalid preset_id format: {preset_id}")
            abort(400, description="preset_id must be a number")

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


@app.route('/reset_preferences', methods=['POST'])
def reset_preferences():
    """ Reset user model preferences to defaults """
    try:
        data = request.get_json()
        preset_id = data.get('preset_id') if data else None
        user_identifier = get_user_identifier()
        from models import UserPreference 

        if preset_id:
            # Reset only the specific preset
            try:
                preset_id = int(preset_id)
                if not 1 <= preset_id <= 6: 
                    abort(400, description="preset_id must be between 1 and 6")
                # Delete the specific preference
                UserPreference.query.filter_by(
                    user_identifier=user_identifier, 
                    preset_id=preset_id
                ).delete()
                message = f"Preference for preset {preset_id} reset to default"
            except ValueError: 
                abort(400, description="preset_id must be a number")
        else:
            # Reset all presets
            UserPreference.query.filter_by(user_identifier=user_identifier).delete()
            message = "All preferences reset to defaults"
        
        db.session.commit()
        return jsonify({"success": True, "message": message})
    except Exception as e:
        logger.exception("Error resetting preferences")
        db.session.rollback()
        abort(500, description=str(e))


@app.route('/conversation/<int:conversation_id>/messages', methods=['GET'])
@login_required
def get_conversation_messages(conversation_id):
    """ Get all messages for a specific conversation """
    try:
        from models import Conversation, Message 
        
        # Check if conversation exists
        conversation = db.session.get(Conversation, conversation_id)
        if not conversation:
            abort(404, description="Conversation not found")
            
        # Verify the conversation belongs to the current user
        if conversation.user_id != current_user.id:
            abort(403, description="You don't have permission to access this conversation")
            
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
                "model": msg.model,
                "image_url": msg.image_url  # Include image URL for multimodal messages
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
@login_required
def rate_message(message_id):
    """ Rate a message """
    try:
        data = request.get_json()
        if not data: abort(400, description="Invalid request body. JSON expected.")
        rating = data.get('rating')
        if rating is None or rating not in [1, -1, 0]: abort(400, description="Rating must be 1, -1, or 0")

        from models import Message, Conversation
        message = db.session.get(Message, message_id) 
        if not message: abort(404, description="Message not found")
        
        # Check if the message belongs to a conversation owned by the current user
        conversation = db.session.get(Conversation, message.conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            abort(403, description="You don't have permission to rate this message")

        message.rating = rating if rating in [1, -1] else None 
        db.session.commit()
        logger.info(f"Saved rating {rating} for message {message_id}")
        return jsonify({"success": True, "message": "Rating saved"})
    except Exception as e:
        logger.exception(f"Error saving rating for message {message_id}")
        db.session.rollback()
        abort(500, description=str(e))


@app.route('/conversation/<int:conversation_id>/share', methods=['POST']) 
@login_required
def share_conversation(conversation_id):
    """ Generate or retrieve share link """
    try:
        from models import Conversation 
        conversation = db.session.get(Conversation, conversation_id) 
        if not conversation: abort(404, description="Conversation not found")
        
        # Verify the conversation belongs to the current user
        if conversation.user_id != current_user.id:
            abort(403, description="You don't have permission to share this conversation")

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

@app.route('/csrf_test', methods=['GET'])
def csrf_test_page():
    """
    Test page for CSRF token handling
    """
    return render_template('csrf_test.html')

@app.route('/api/test_csrf', methods=['POST'])
def test_csrf():
    """
    Test endpoint for CSRF token verification
    """
    # If we get here, CSRF protection passed
    data = request.get_json() or request.form.to_dict() or {}
    return jsonify({
        'success': True,
        'message': 'CSRF token verification successful',
        'received_data': data
    })

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
    
    # Perform initial model price fetch
    try:
        logger.info("Performing initial model price fetch on startup")
        fetch_and_store_openrouter_prices()
    except Exception as e:
        logger.error(f"Error during initial model price fetch: {e}")
    
    # Start the price update scheduler
    scheduler.start()
    logger.info("Started background scheduler for model price updates")
    
    # ensure gevent monkey-patching already happened at import time
    app.run(host='0.0.0.0', port=5000, debug=True)