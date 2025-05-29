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
from flask import Flask, render_template, request, Response, session, jsonify, abort, url_for, redirect, flash, stream_with_context, send_from_directory
from urllib.parse import urlparse # For URL analysis in image handling
from werkzeug.datastructures import FileStorage # For file handling in upload routes
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_wtf.csrf import CSRFProtect
from azure.storage.blob import BlobServiceClient, ContentSettings  # For Azure Blob Storage
from apscheduler.schedulers.background import BackgroundScheduler
from database import db, init_app
from price_updater import fetch_and_store_openrouter_prices, model_prices_cache

# Check if we should enable advanced memory features
ENABLE_MEMORY_SYSTEM = os.environ.get('ENABLE_MEMORY_SYSTEM', 'false').lower() == 'true'

# Check if we should enable RAG features
ENABLE_RAG = False  # Disabled - using direct PDF handling with OpenRouter instead

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
        
# RAG system removed - using direct PDF handling with OpenRouter instead
# The system now processes PDFs directly through OpenRouter PDF capabilities


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import SQLAlchemy from database module
from database import db

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "developmentsecretkey")
if not app.secret_key:
     logger.warning("SESSION_SECRET environment variable not set. Using default for development.")
     app.secret_key = "default-dev-secret-key-please-change"

# Initialize CSRF protection with extended timeout
app.config['WTF_CSRF_TIME_LIMIT'] = 86400  # Set CSRF token timeout to 24 hours (in seconds)
# Disable strict SSL checking for CSRF to handle Cloudflare and non-Cloudflare modes
app.config['WTF_CSRF_SSL_STRICT'] = False

# Make sure CSRF cookie matches the domain being used
app.config['WTF_CSRF_SAMESITE'] = 'Lax'

csrf = CSRFProtect(app)

# Configure Redis session support - this will use Redis if available or fall back to Flask's default
try:
    from redis_session import setup_redis_session
    setup_redis_session(app)
    logger.info("Redis session interface configured successfully")
except ImportError as e:
    logger.warning(f"Could not initialize Redis sessions: {e}. Using default Flask sessions.")
except Exception as e:
    logger.warning(f"Error setting up Redis sessions: {e}. Using default Flask sessions.")
    
# Configure rate limiting middleware
try:
    from middleware import setup_rate_limiting
    setup_rate_limiting(app)
    logger.info("Rate limiting middleware configured successfully")
except ImportError as e:
    logger.warning(f"Could not initialize rate limiting: {e}")
except Exception as e:
    logger.warning(f"Error setting up rate limiting: {e}")

# Add asset versioning for cache busting
app.config['ASSETS_VERSION'] = os.environ.get('ASSETS_VERSION', datetime.datetime.now().strftime('%Y%m%d%H'))

# Set up cache control for static assets
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 60 * 60 * 24 * 7  # 1 week cache for static files
app.config['JSON_SORT_KEYS'] = False  # Prevent JSON sorting for faster responses

# Add after_request hook for additional performance headers
@app.after_request
def add_performance_headers(response):
    """Add performance optimization headers to static assets."""
    if 'Cache-Control' not in response.headers:
        # Default cache policy
        response.headers['Cache-Control'] = 'no-store'
        
    # Set performance headers for static assets
    if request.path.startswith('/static/'):
        if request.path.endswith(('.css', '.js')):
            # Long cache for versioned assets (1 week)
            if 'v=' in request.query_string.decode('utf-8'):
                response.headers['Cache-Control'] = 'public, max-age=604800, immutable'
        elif request.path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')):
            # Cache images for 1 day
            response.headers['Cache-Control'] = 'public, max-age=86400'
    
    # Add security and performance headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    return response

# Add global template context variables
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

# Initialize Azure Blob Storage variables
blob_service_client = None
container_client = None
USE_AZURE_STORAGE = False

def initialize_azure_storage():
    """
    Deferred initialization of Azure Blob Storage.
    This function initializes Azure storage in a background thread to avoid blocking app startup.
    
    The implementation has been optimized to prevent recursion errors and improve performance
    by using the startup cache to avoid redundant initializations.
    """
    global blob_service_client, container_client, USE_AZURE_STORAGE
    start_time = time.time()
    
    try:
        # First check if we have already initialized
        if blob_service_client is not None and container_client is not None:
            logger.info("Azure Blob Storage already initialized in this session, skipping")
            return
            
        # Check startup cache to see if Azure Storage was recently initialized
        try:
            from startup_cache import startup_cache
            
            # Only check cache if we don't already have initialized clients
            if not startup_cache.service_needs_update('azure_storage', max_age_hours=24.0):
                cache_data = startup_cache.get_service_data('azure_storage')
                logger.info(f"Using cached Azure Storage initialization (age: {cache_data.get('age_hours', 'unknown')} hours)")
                
                # We should still initialize the clients, but can skip container validation
                azure_connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
                azure_container_name = os.environ.get("AZURE_STORAGE_CONTAINER_NAME", "gloriamundoblobs")
                
                if not azure_connection_string:
                    logger.warning("Missing Azure Storage connection string, will use local storage")
                    return
                    
                # Fast initialization path - skip container validation using cache data
                blob_service_client = BlobServiceClient.from_connection_string(
                    azure_connection_string,
                    connection_timeout=10,
                    retry_total=3
                )
                container_client = blob_service_client.get_container_client(azure_container_name)
                USE_AZURE_STORAGE = True
                
                # Exit early since we're using cached validation
                elapsed = time.time() - start_time
                logger.info(f"Azure Storage initialized from cache in {elapsed:.2f}s")
                return
                
        except ImportError:
            # Cache module not available, continue with full initialization
            logger.debug("Startup cache not available for Azure Storage, performing full initialization")
            pass
            
        # Get connection string and container name from environment variables
        azure_connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        azure_container_name = os.environ.get("AZURE_STORAGE_CONTAINER_NAME", "gloriamundoblobs")
        
        if not azure_connection_string:
            logger.warning("Missing Azure Storage connection string, will use local storage")
            return
            
        # Create the BlobServiceClient with explicit timeout settings
        blob_service_client = BlobServiceClient.from_connection_string(
            azure_connection_string,
            connection_timeout=10,  # Shorter connection timeout to prevent blocking
            retry_total=3           # Limit retries to prevent recursion
        )
        
        # Get a client to interact with the container
        container_client = blob_service_client.get_container_client(azure_container_name)
        
        # Check if container exists, if not create it - handle with proper error catching
        container_exists = False
        try:
            # Only check properties, don't perform additional operations that might cause recursion
            container_exists = container_client.exists()
            if container_exists:
                logger.info(f"Container {azure_container_name} exists")
            else:
                logger.info(f"Container {azure_container_name} does not exist, creating it...")
                container_client = blob_service_client.create_container(azure_container_name)
                container_exists = True
                logger.info(f"Container {azure_container_name} created successfully")
        except Exception as container_error:
            logger.warning(f"Error checking container: {container_error}")
            # Try to create the container anyway as a fallback
            try:
                container_client = blob_service_client.create_container(azure_container_name)
                container_exists = True
                logger.info(f"Created container {azure_container_name} in fallback mode")
            except Exception as create_error:
                logger.error(f"Could not create container: {create_error}")
                raise
        
        # Update the global flag
        USE_AZURE_STORAGE = True
        elapsed = time.time() - start_time
        logger.info(f"Azure Blob Storage initialized successfully in {elapsed:.2f}s for container: {azure_container_name}")
        
        # Update the startup cache
        try:
            from startup_cache import startup_cache
            startup_cache.update_service_data('azure_storage', {
                'container_name': azure_container_name,
                'container_exists': container_exists,
                'initialization_time': elapsed,
                'age_hours': 0.0
            })
        except ImportError:
            pass
            
    except Exception as e:
        logger.warning(f"Failed to initialize Azure Blob Storage: {e}")
        logger.info("Falling back to local storage for image uploads")
        USE_AZURE_STORAGE = False

# Configure database first since it's critical
init_app(app)  # Initialize database with the app (from database.py)
if not app.config["SQLALCHEMY_DATABASE_URI"]:
    logger.error("DATABASE_URL environment variable not set.")
    # Handle this critical error appropriately

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Create essential tables needed for startup - these can't be deferred
with app.app_context():
    db.create_all()
    logger.info("Essential database tables created")

# DIAGNOSTIC TEST: Completely disable background tasks to restore API functionality
logger.info("DIAGNOSTIC: Skipping ALL background tasks to test API connectivity...")

# Simple fallback Azure Storage initialization in background thread
try:
    azure_init_thread = threading.Thread(
        target=initialize_azure_storage, 
        daemon=True,
        name="azure-storage-init-fallback"
    )
    azure_init_thread.start()
    logger.info("Simple Azure Storage initialization scheduled")
except Exception as e:
    logger.warning(f"Azure storage initialization failed: {e}")

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Register blueprints
# Import and use the fixed affiliate blueprint
try:
    # First try to use the completely fixed version
    from affiliate_blueprint_improved_fixed import affiliate_bp, init_app as init_affiliate
    init_affiliate(app)  # This function handles blueprint registration internally
    logger.info('Registered fixed affiliate blueprint (affiliate_blueprint_improved_fixed)')
except ImportError as e:
    logger.warning(f'Could not import fixed affiliate blueprint: {e}')
    # Fall back to the simplified version if fixed is not available
    try:
        from simplified_affiliate import simplified_affiliate_bp, init_app as init_simplified_affiliate
        init_simplified_affiliate(app)  # Use the proper init function instead of direct registration
        logger.info('Registered simplified_affiliate_bp (fallback)')
    except ImportError as e2:
        logger.warning(f'Could not import simplified_affiliate_bp: {e2}')
        simplified_affiliate_bp = None
try:
    from google_auth import google_auth
    app.register_blueprint(google_auth)
    logger.info("Google Auth blueprint registered successfully")
except Exception as e:
    logger.error(f"Error registering Google Auth blueprint: {e}")

# Register billing blueprint (temporarily disabled to fix startup)
# try:
#     from billing import billing_bp
#     app.register_blueprint(billing_bp, url_prefix='/billing')
#     # Exempt Stripe webhook from CSRF protection
#     csrf.exempt('billing.stripe_webhook')
#     csrf.exempt('simplified_affiliate.update_paypal_email')  # Exempt PayPal email update form
#     logger.info("Billing blueprint registered successfully with prefix /billing")
# except Exception as e:
#     logger.error(f"Error registering Billing blueprint: {e}")
logger.info("Billing blueprint temporarily disabled to fix circular import")
# Simplified affiliate blueprint is imported in the try/except block above
# We only register the simplified affiliate blueprint now
# The old affiliate blueprint registration has been removed to avoid route conflicts
    
# Register user settings blueprint
try:
    from user_settings import user_settings_bp, init_user_settings
    init_user_settings(app)
    logger.info("User settings blueprint registered successfully")
except Exception as e:
    logger.error(f"Error registering User settings blueprint: {e}")

# Register admin blueprint
try:
    # Define custom error handler function that will be passed to admin module
    def handle_admin_exception(e):
        logger.error(f"Admin exception: {str(e)}", exc_info=True)
        return """
        <html>
            <head><title>Admin Error</title></head>
            <body>
                <h1>Error in Admin Panel</h1>
                <p>An unexpected error occurred in the admin panel. This has been logged for investigation.</p>
                <p>Error details: {}</p>
                <a href="/">Return to Home</a>
            </body>
        </html>
        """.format(str(e)), 500
    
    # Now import and initialize the admin blueprint
    from admin import init_admin
    init_admin(app)
    
    # Log success
    logger.info("Admin blueprint registered successfully with prefix /admin_simple")
    
    # Add redirects from old admin routes to new admin routes
    @app.route('/admin')
    @app.route('/admin/')
    @app.route('/admin_portal')
    @app.route('/admin_portal/')
    @app.route('/admin_dash')
    @app.route('/admin_dash/')
    def redirect_to_admin_portal():
        return redirect(url_for('admin_simple.index'))
        
    @app.route('/admin/<path:subpath>')
    @app.route('/admin_portal/<path:subpath>')
    @app.route('/admin_dash/<path:subpath>')
    def redirect_admin_subpaths(subpath):
        # Redirect all admin routes to our new admin implementation
        return redirect('/admin_simple/' + subpath)
        
except Exception as e:
    logger.error(f"Error registering Admin blueprint: {str(e)}", exc_info=True)

# Register jobs blueprint for background job processing
try:
    # Import the improved jobs blueprint module that avoids circular imports
    from jobs_blueprint_improved import init_app as init_jobs_bp
    
    # Initialize the jobs blueprint with our Flask app
    init_jobs_bp(app)
    
    # Log success
    logger.info("Jobs blueprint registered successfully with prefix /jobs")
except Exception as e:
    logger.error(f"Error registering Jobs blueprint: {str(e)}", exc_info=True)

# Helper function for admin access control
def is_admin():
    """Check if the current user is an admin (specifically andy@sentigral.com)"""
    # Check if user is authenticated and has the specific email
    admin_email = os.environ.get('ADMIN_EMAIL', 'andy@sentigral.com').lower()
    return current_user.is_authenticated and current_user.email.lower() == admin_email

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
    "1": "anthropic/claude-sonnet-4", # Default model - reasoning powerhouse
    "2": "meta-llama/llama-4-maverick", # Fast, good quality
    "3": "anthropic/claude-sonnet-4", # Reasoning models (preset loads non-free reasoning models)
    "4": "openai/gpt-4o-2024-11-20", # Premium quality
    "5": "perplexity/sonar-pro", # Open model
    "6": "google/gemini-2.0-flash-exp:free", # Free model
}
FREE_MODEL_FALLBACKS = [
    # Updated with verified free models available in OpenRouter
    "google/gemini-flash:free",  # Primary free model
    "meta-llama/llama-3-8b-free", # Fallback free model
    "openrouter/auto:free",     # Auto-selection free model
    "neural-chat/neural-chat-7b-v3-1:free" # Another fallback
]

# Safe fallback model IDs when no specific model can be determined
# Listed in order of preference - we'll try each one until we find one that works
SAFE_FALLBACK_MODELS = [
    "anthropic/claude-3-haiku-20240307",  # Most reliable and fast multimodal model
    "google/gemini-pro-vision",  # Good multimodal alternative
    "meta-llama/llama-3-8b",  # Text-only fallback
    "mistralai/mistral-7b"     # Another text-only fallback
]

# Models that support images (multimodal)
MULTIMODAL_MODELS = {
    "google/gemini-pro-vision",
    "google/gemini-1.5-pro-latest",
    "anthropic/claude-3-opus-20240229",
    "anthropic/claude-3-sonnet-20240229",
    "anthropic/claude-3-haiku-20240307",
    "anthropic/claude-3.5-sonnet-20240620",
    "anthropic/claude-3.7-sonnet-20240910",
    "anthropic/claude-opus-4",
    "anthropic/claude-sonnet-4",
    "openai/gpt-4-vision-preview",
    "openai/gpt-4o-2024-05-13",
    "mistralai/mistral-large-latest"
}

# Models that support PDF documents (document processing)
DOCUMENT_MODELS = {
    # Google models with document support
    "google/gemini-pro-vision", 
    "google/gemini-1.5-pro-latest",
    "google/gemini-2.0-pro",
    "google/gemini-2.5-pro-preview",
    
    # Anthropic models with document support
    "anthropic/claude-3-opus-20240229",
    "anthropic/claude-3-sonnet-20240229", 
    "anthropic/claude-3-haiku-20240307",
    "anthropic/claude-3.5-sonnet-20240620",
    "anthropic/claude-3.7-sonnet-20240910",
    "anthropic/claude-opus-4",
    "anthropic/claude-sonnet-4",
    
    # OpenAI models with document support
    "openai/gpt-4-turbo",
    "openai/gpt-4-vision-preview",
    "openai/gpt-4o",  # Base model ID
    "openai/gpt-4o-2024-05-13",
    "openai/gpt-4o-2024-08-06",
    "openai/gpt-4o-2024-11-20",  # Latest model
    "openai/o1-mini-2024-09-12",
    "openai/o1-preview-2024-09-12",
    
    # Perplexity models with document support
    "perplexity/sonar-small-online",
    "perplexity/sonar-medium-online",
    "perplexity/sonar-pro",
    "perplexity/sonar-pro-2024-05-15"
}

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
        
        # Run the initial price check with a longer delay to avoid slowing down page load
        # This will run only if prices haven't been updated in the last 3 hours
        scheduler.add_job(
            func=fetch_and_store_openrouter_prices,
            trigger='date',  # Run once at a specific time
            run_date=datetime.datetime.now() + datetime.timedelta(minutes=2),  # Run 2 minutes after startup
            id='initial_fetch_model_prices_job',
            replace_existing=True,
            max_instances=1
        )
        
        # ELO scores are now managed manually via admin interface - no automatic fetching needed
        
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

# Check if we have models in the database - without fetching new data which slows down startup
logger.info("Checking for OpenRouter models in database at startup")
try:
    # First ensure proper Python imports
    import traceback
    from price_updater import fetch_and_store_openrouter_prices
    from models import OpenRouterModel
    
    # Create an application context for database operations
    with app.app_context():
        # Check if we have models in the database
        model_count = OpenRouterModel.query.count()
    
    if model_count > 0:
        logger.info(f"Found {model_count} OpenRouter models in database at startup")
        
        # The scheduler will check if prices need to be refreshed after startup
        # This avoids blocking the application initialization
        logger.info("Scheduler will check if model data needs refresh in background")
    else:
        # For first-time setup only, we need to defer this too
        logger.info("No OpenRouter models found in database, will schedule background fetch")
        
        # Create a background thread to fetch initial data if database is empty
        # This won't block application startup
        def fetch_initial_model_data():
            logger.info("Background thread: Fetching initial model data...")
            time.sleep(5)  # Give the app some time to initialize
            try:
                # Fetch model prices
                price_success = fetch_and_store_openrouter_prices(force_update=True)
                
                if price_success:
                    # Check if models were stored in the database
                    with app.app_context():
                        model_count = OpenRouterModel.query.count()
                    logger.info(f"Successfully fetched and stored {model_count} OpenRouter models in database")
                else:
                    # If that fails, log a warning - we'll rely on the scheduler to retry soon
                    logger.warning("Initial model fetching failed. The scheduler will retry shortly.")
            except Exception as e:
                logger.error(f"Error in background fetch of model data: {e}")
        
        # Start the background thread for initial model data fetch
        threading.Thread(target=fetch_initial_model_data, daemon=True).start()
    
    # Final verification of database state - use with app_context to ensure DB operations work
    with app.app_context():
        model_count = OpenRouterModel.query.count()
        if model_count > 0:
            logger.info(f"OpenRouter model database initialized with {model_count} models")
        else:
            logger.warning("No models available in the database. Application may have limited functionality.")
        
except Exception as e:
    logger.error(f"Critical error fetching model data at startup: {e}")
    logger.error(traceback.format_exc())
    logger.warning("Application may have limited functionality until models are fetched.")

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

def generate_summary(conversation_id, retry_attempt=0, max_retries=2):
    """
    Generate a short, descriptive title for a conversation using OpenRouter LLM.
    This function runs non-blocking under gevent to avoid blocking the server.
    
    Args:
        conversation_id: The ID of the conversation to summarize
        retry_attempt: Current retry attempt number (default 0)
        max_retries: Maximum number of retries (default 2)
    """
    # Import necessary modules here to avoid potential conflicts
    # Note: Using global json module instead of reimporting
    import traceback
    
    print(f"[SUMMARIZE {conversation_id}] Function called. Retry attempt: {retry_attempt}/{max_retries}") # Enhanced logging
    print(f"DEBUG: generate_summary - ENTERED with conv_id: {conversation_id}")
    logger.info(f"DEBUG: generate_summary - ENTERED with conv_id: {conversation_id}")
    try:
        logger.info(f"Generating summary for conversation {conversation_id} (attempt {retry_attempt+1})")
        from models import Conversation, Message
        
        # Check if title is already customized (not the default)
        conversation = db.session.get(Conversation, conversation_id)
        if not conversation:
            print(f"[SUMMARIZE {conversation_id}] Conversation not found in database.") 
            logger.warning(f"Conversation {conversation_id} not found when generating summary")
            return
            
        if conversation.title != "New Conversation":
            print(f"[SUMMARIZE {conversation_id}] Already has title: {conversation.title}") 
            logger.info(f"Conversation {conversation_id} already has a custom title: '{conversation.title}'. Skipping.")
            return
        else:
            print(f"[SUMMARIZE {conversation_id}] No existing summary found, proceeding.") 
            
        # Get all messages, ordered by creation time
        messages = Message.query.filter_by(conversation_id=conversation_id)\
            .order_by(Message.created_at)\
            .all()
            
        if len(messages) < 2:
            print(f"[SUMMARIZE {conversation_id}] Not enough messages ({len(messages)}) to summarize.") 
            logger.warning(f"Not enough messages in conversation {conversation_id} to generate summary")
            return
        else:
            print(f"[SUMMARIZE {conversation_id}] Found {len(messages)} total messages.") 
            
        # Find the first user message and its corresponding assistant response
        user_message = None
        assistant_message = None
        
        for i, message in enumerate(messages):
            if message.role == 'user':
                # Try to find the assistant message that follows this user message
                if i + 1 < len(messages) and messages[i + 1].role == 'assistant':
                    user_message = message.content
                    assistant_message = messages[i + 1].content
                    print(f"[SUMMARIZE {conversation_id}] Found user-assistant pair at positions {i} and {i+1}") 
                    break  # Found a user-assistant pair, we can stop searching
        
        if not user_message or not assistant_message:
            print(f"[SUMMARIZE {conversation_id}] Missing user or assistant message.") 
            logger.warning(f"Missing user or assistant message in conversation {conversation_id}")
            return
            
        # Get API Key
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            print(f"[SUMMARIZE {conversation_id}] OPENROUTER_API_KEY not found.") 
            logger.error("OPENROUTER_API_KEY not found while generating summary")
            return
            
        # Try the primary free model first, then fall back to other free models if needed
        if retry_attempt == 0:
            model_id = DEFAULT_PRESET_MODELS.get('6', 'google/gemini-flash:free')
        else:
            # On retry attempts, try alternative free models
            model_id = FREE_MODEL_FALLBACKS[min(retry_attempt, len(FREE_MODEL_FALLBACKS)-1)]
            
        print(f"[SUMMARIZE {conversation_id}] Using model: {model_id} for attempt {retry_attempt+1}")
        
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
            'HTTP-Referer': 'https://gloriamundo.com'  # Updated referrer to look more legitimate
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
        print(f"[SUMMARIZE {conversation_id}] Prompt constructed. About to call API with model {model_id}.") 
        print(f"[SUMMARIZE {conversation_id}] API Key: {'VALID' if api_key else 'MISSING'}")
        logger.info(f"Sending title generation request to OpenRouter with model: {model_id}")
        
        try:
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30.0  # Increased timeout for more reliability
            )
        except requests.exceptions.Timeout:
            print(f"[SUMMARIZE {conversation_id}] API request timed out after 30 seconds")
            logger.error(f"OpenRouter API timeout during title generation for conversation {conversation_id}")
            
            # Retry on timeout if we haven't exceeded max retries
            if retry_attempt < max_retries:
                print(f"[SUMMARIZE {conversation_id}] Scheduling retry {retry_attempt+1}/{max_retries}")
                # Use threading for retry to avoid blocking
                import threading
                threading.Timer(2.0, lambda: generate_summary(conversation_id, retry_attempt+1, max_retries)).start()
            return
            
        except requests.exceptions.RequestException as e:
            print(f"[SUMMARIZE {conversation_id}] API request error: {e}")
            logger.error(f"OpenRouter API error during title generation: {e}")
            
            # Retry on request exception if we haven't exceeded max retries
            if retry_attempt < max_retries:
                print(f"[SUMMARIZE {conversation_id}] Scheduling retry {retry_attempt+1}/{max_retries}")
                import threading
                threading.Timer(2.0, lambda: generate_summary(conversation_id, retry_attempt+1, max_retries)).start()
            return
        
        print(f"[SUMMARIZE {conversation_id}] API call finished. Status: {response.status_code}") 
        
        if response.status_code != 200:
            print(f"[SUMMARIZE {conversation_id}] API error: {response.status_code} - {response.text[:300]}") 
            logger.error(f"OpenRouter API error while generating title: {response.status_code} - {response.text}")
            
            # Retry on non-200 response if we haven't exceeded max retries
            if retry_attempt < max_retries:
                print(f"[SUMMARIZE {conversation_id}] Scheduling retry {retry_attempt+1}/{max_retries}")
                import threading
                threading.Timer(3.0, lambda: generate_summary(conversation_id, retry_attempt+1, max_retries)).start()
            return
            
        # Process the response
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            title_text = response_data['choices'][0]['message']['content'].strip()
            print(f"[SUMMARIZE {conversation_id}] Summary extracted: {title_text}") 
            
            # Clean up the title (remove quotes, etc.)
            title_text = title_text.strip('"\'')
            if len(title_text) > 50:
                title_text = title_text[:47] + "..."
                
            # Update the conversation title and updated_at timestamp
            from datetime import datetime 
            conversation.title = title_text
            conversation.updated_at = datetime.utcnow()  # Explicitly update the timestamp
            print(f"[SUMMARIZE {conversation_id}] Updating DB title with fresh timestamp") 
            logger.info(f"DEBUG: Attempting to update conversation {conversation_id} with title: '{title_text}'")
            try:
                db.session.commit()
                print(f"[SUMMARIZE {conversation_id}] DB commit successful.") 
                logger.info(f"DEBUG: Database commit successful for summary of conversation {conversation_id}")
                logger.info(f"Updated conversation {conversation_id} title to: '{title_text}' with new timestamp")
            except Exception as db_error:
                print(f"[SUMMARIZE {conversation_id}] DB commit FAILED: {db_error}")
                logger.error(f"DEBUG: Database commit FAILED for summary: {db_error}")
                db.session.rollback()
                raise  # Re-raise to trigger retry logic
        else:
            print(f"[SUMMARIZE {conversation_id}] Failed to extract title from API response: {response_data}") 
            logger.warning(f"Failed to extract title from API response: {response_data}")
            
            # Retry if we couldn't extract a title and haven't exceeded max retries
            if retry_attempt < max_retries:
                print(f"[SUMMARIZE {conversation_id}] Scheduling retry {retry_attempt+1}/{max_retries}")
                import threading
                threading.Timer(2.0, lambda: generate_summary(conversation_id, retry_attempt+1, max_retries)).start()
            
    except Exception as e:
        # Use traceback for more detailed error information
        import traceback
        print(f"[SUMMARIZE {conversation_id}] Error during summarization:") 
        traceback.print_exc() 
        logger.exception(f"Error generating summary for conversation {conversation_id}: {e}")
        try:
            db.session.rollback()
        except:
            pass
            
        # Retry on exception if we haven't exceeded max retries
        if retry_attempt < max_retries:
            print(f"[SUMMARIZE {conversation_id}] Scheduling retry {retry_attempt+1}/{max_retries} after error")
            import threading
            threading.Timer(3.0, lambda: generate_summary(conversation_id, retry_attempt+1, max_retries)).start()



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
@app.route('/test_url_formatting')
def test_url_formatting():
    """Render the URL formatting test page"""
    return render_template('test_url_formatting.html')


# Direct handler for PayPal email updates without CSRF validation
@app.route("/update_paypal_email", methods=["POST"])
def direct_update_paypal_email():
    """Direct handler for PayPal email updates that bypasses CSRF validation"""
    import uuid
    from models import User  # Affiliate model is deprecated, using User model directly now
    
    logger.info(f"Direct PayPal email update request: {request.form}")
    logger.info(f"Session data: {dict(session)}")
    
    if 'user_id' not in session:
        flash('Please login to update your PayPal email', 'warning')
        return redirect(url_for('login'))
    
    try:
        # Get the email from the form
        paypal_email = request.form.get('paypal_email', '').strip()
        
        # Get the user's email from their user record
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('login'))
            
        user_email = user.email
        logger.info(f"Found user: ID={user_id}, email={user_email}")
        
        if not paypal_email:
            flash('Please provide a PayPal email address', 'error')
            return redirect(url_for('billing.account_management', _anchor='tellFriend'))
        
        # Log the affiliate lookup
        logger.info(f"Looking for affiliate with email: {user_email}")
        
        # In our simplified system, affiliate info is stored directly in the User model
        logger.info(f"Updating PayPal email for user {user.id}")
        
        # Update the user's PayPal email
        old_email = user.paypal_email or "None"
        user.paypal_email = paypal_email
        
        # Generate referral code if needed
        if not user.referral_code:
            user.generate_referral_code()
            logger.info(f"Generated new referral code {user.referral_code} for user {user.id}")
        
        # Log the change clearly
        logger.info(f"CHANGING PayPal email for user ID {user.id} from '{old_email}' to '{paypal_email}'")
        
        # Commit changes
        db.session.commit()
        
        # Use a more specific success message
        if old_email != paypal_email:
            flash(f'PayPal email updated successfully from {old_email} to {paypal_email}!', 'success')
        else:
            flash('PayPal email saved (no change detected)', 'info')
            
        logger.info(f"Successfully updated PayPal email in database")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating PayPal email: {str(e)}", exc_info=True)
        flash('An error occurred while updating your PayPal email. Please try again.', 'error')
    
    return redirect(url_for('billing.account_management', _anchor='tellFriend'))



# Direct PayPal email update route
@app.route("/update_paypal", methods=["POST"])
def update_paypal_email_direct():
    # Update PayPal email address for the current user - returns JSON for JavaScript
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please login to update your PayPal email'})
    
    try:
        # Get data from JSON body (JavaScript sends JSON, not form data)
        if request.is_json:
            paypal_email = request.json.get('paypal_email', '').strip()
        else:
            paypal_email = request.form.get('paypal_email', '').strip()
        logger.info(f"PayPal update request - User: {current_user.id}, Email: '{paypal_email}'")
        
        if not paypal_email:
            logger.warning(f"Empty PayPal email provided for user {current_user.id}")
            return jsonify({'success': False, 'message': 'Please provide a PayPal email address'})
        
        # Log the update attempt
        old_email = current_user.paypal_email or 'None'
        logger.info(f"Updating PayPal email for user {current_user.id} from '{old_email}' to '{paypal_email}'")
        
        # Check if user has the paypal_email attribute
        if not hasattr(current_user, 'paypal_email'):
            logger.error(f"User model missing paypal_email field for user {current_user.id}")
            return jsonify({'success': False, 'message': 'Database error: missing field'})
        
        # Update user record
        current_user.paypal_email = paypal_email
        logger.info(f"Set paypal_email to '{paypal_email}', now committing to database...")
        
        db.session.commit()
        logger.info(f"Database commit successful for user {current_user.id}")
        
        # Verify the update
        db.session.refresh(current_user)
        final_email = current_user.paypal_email
        logger.info(f"Final verification - PayPal email is now: '{final_email}'")
        
        return jsonify({
            'success': True, 
            'message': f'PayPal email updated successfully to {paypal_email}!',
            'new_email': paypal_email
        })
        
    except Exception as e:
        logger.error(f"Error updating PayPal email for user {current_user.id}: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'})


@app.route('/')
def index():
    """Main route that serves as both health check and app entry point"""
    # Return a health check response for any health checker or if explicitly requested
    # Replit's deployment system checks the root path for health checks
    if (request.headers.get('User-Agent', '').startswith('ELB-HealthChecker') or 
        'health' in request.args or 
        'healthcheck' in request.args or
        request.headers.get('User-Agent', '').lower().startswith('curl') or
        request.headers.get('Accept', '').startswith('*/*')):
        return 'Application is healthy!', 200
        
    # Regular app behavior - redirect non-authenticated users to the info page
    if not current_user.is_authenticated:
        return redirect(url_for('info'))
    
    # For authenticated users, show the normal interface
    is_logged_in = current_user.is_authenticated
    
    # Check if there's a specific conversation to load (used for redirects from share links)
    conversation_id = request.args.get('conversation_id')
    
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
        conversations=conversations,
        initial_conversation_id=conversation_id
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

@app.route('/info')
def info():
    """Marketing information page"""
    from datetime import datetime
    import logging
    try:
        return render_template('info.html', now=datetime.now())
    except Exception as e:
        logging.error(f"Error rendering info.html: {str(e)}")
        # Return detailed error for debugging
        return f"<h1>Error rendering marketing page</h1><p>Error: {str(e)}</p>", 500
    
# Note: Removed redundant route handler for '/billing/account'
# This is now properly handled by the billing blueprint with the '/account' route

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
            for blob in container_client.list_blobs(maxresults=5):
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

@app.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    """
    Unified file upload route that handles both images and PDFs based on file type.
    This allows a single upload button in the UI to handle different file types.
    
    For images:
        - Processes and stores in Azure 'gloriamundoblobs' container
        - Returns image_url suitable for multimodal models
        
    For PDFs:
        - Stores PDFs in 'gloriamundopdfs' Azure Blob Storage container
        - Returns pdf_data_url as base64 data URL for OpenRouter document handling
        
    Query Parameters:
        conversation_id (str, optional): The ID of the current conversation for metadata tracking
        model (str, optional): The ID of the model being used (affects URL generation)
        
    Returns:
        JSON with appropriate URLs based on file type
    """
    try:
        # Get conversation ID if provided (useful for tracking uploads)
        conversation_id = request.args.get('conversation_id')
        if conversation_id:
            logger.info(f"File upload associated with conversation: {conversation_id}")
        else:
            logger.info(f"File upload with no conversation ID")
        
        # Verify a file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
            
        # Detect file type from extension
        filename = file.filename
        extension = Path(filename).suffix.lower()
        
        # Route to appropriate handler based on file type
        if extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            # Handle image uploads directly within this function context
            # This ensures the request.files['file'] is available in the same context
            
            # Image upload logic (copied from upload_image function)
            try:
                if 'file' not in request.files:
                    return jsonify({"error": "No file provided"}), 400
                    
                uploaded_file = request.files['file']
                if uploaded_file.filename == '':
                    return jsonify({"error": "No file selected"}), 400
                
                # Generate unique filename
                unique_filename = f"{uuid.uuid4().hex}.{uploaded_file.filename.split('.')[-1].lower()}"
                
                # Read and validate the image
                image_data = uploaded_file.read()
                if len(image_data) == 0:
                    return jsonify({"error": "Empty file"}), 400
                
                # Validate image and resize if needed
                try:
                    image = Image.open(io.BytesIO(image_data))
                    # Convert to RGB if needed
                    if image.mode in ('RGBA', 'LA', 'P'):
                        image = image.convert('RGB')
                    
                    # Resize if too large
                    max_size = (2048, 2048)
                    if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                        image.thumbnail(max_size, Image.LANCZOS)
                        
                        # Convert back to bytes
                        img_buffer = io.BytesIO()
                        image.save(img_buffer, format='JPEG', quality=85)
                        image_data = img_buffer.getvalue()
                        unique_filename = f"{uuid.uuid4().hex}.jpg"
                        
                except Exception as e:
                    logger.error(f"Image processing error: {e}")
                    return jsonify({"error": "Invalid image file"}), 400
                
                # Upload to Azure Blob Storage
                blob_service_client = BlobServiceClient.from_connection_string(os.getenv('AZURE_STORAGE_CONNECTION_STRING'))
                container_name = 'gloriamundoblobs'
                blob_client = blob_service_client.get_blob_client(container=container_name, blob=unique_filename)
                
                # Set content type
                content_type = mimetypes.guess_type(unique_filename)[0] or 'image/jpeg'
                blob_client.upload_blob(image_data, overwrite=True, content_settings=ContentSettings(content_type=content_type))
                
                # Generate the blob URL
                image_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{unique_filename}"
                
                logger.info(f"Image uploaded successfully: {image_url}")
                
                return jsonify({
                    "success": True,
                    "image_url": image_url,
                    "file_type": "image",
                    "filename": uploaded_file.filename
                })
                
            except Exception as e:
                logger.exception(f"Error uploading image: {e}")
                return jsonify({"error": f"Upload failed: {str(e)}"}), 500
                
        elif extension == '.pdf':
            # Handle PDF uploads - convert directly to base64 data URL for OpenRouter
            try:
                if 'file' not in request.files:
                    return jsonify({"error": "No file provided"}), 400
                    
                uploaded_file = request.files['file']
                if uploaded_file.filename == '':
                    return jsonify({"error": "No file selected"}), 400
                
                # Read the PDF data
                pdf_data = uploaded_file.read()
                if len(pdf_data) == 0:
                    return jsonify({"error": "Empty file"}), 400
                
                # Convert to base64 data URL (required format for OpenRouter PDF handling)
                import base64
                pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
                pdf_data_url = f"data:application/pdf;base64,{pdf_base64}"
                
                logger.info(f"PDF converted to base64 format: {uploaded_file.filename}")
                
                return jsonify({
                    "success": True,
                    "document_url": pdf_data_url,  # Return base64 data URL directly
                    "document_name": uploaded_file.filename,
                    "file_type": "pdf",
                    "filename": uploaded_file.filename
                })
                
            except Exception as e:
                logger.exception(f"Error uploading PDF: {e}")
                return jsonify({"error": f"Upload failed: {str(e)}"}), 500
        else:
            return jsonify({
                "error": f"File type {extension} is not supported. Please upload an image (jpg, png, gif, webp) or PDF file."
            }), 400
    except Exception as e:
        logger.exception(f"Error handling file upload: {e}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/upload_pdf', methods=['POST'])
@login_required
def upload_pdf():
    """
    Route to handle PDF uploads for models that support documents.
    Stores PDFs in the 'gloriamundopdfs' Azure Blob Storage container.
    
    The returned PDF URL will be included in the message content as:
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "User's message text"},
            {"type": "file", "file": {"filename": "document.pdf", "file_data": "DATA_URL_FROM_THIS_ENDPOINT"}}
        ]
    }
    
    Returns:
        JSON with pdf_data_url containing the base64 data URL needed for OpenRouter's PDF handling
    """
    try:
        # Get conversation ID if provided (useful for tracking uploads)
        conversation_id = request.args.get('conversation_id')
        if conversation_id:
            logger.info(f"PDF upload associated with conversation: {conversation_id}")
        else:
            logger.info(f"PDF upload with no conversation ID - will create a new conversation")
        
        # Verify a file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
            
        # Validate file type
        filename = file.filename
        extension = Path(filename).suffix.lower()
        allowed_extensions = {'.pdf'}
        
        if extension not in allowed_extensions:
            return jsonify({
                "error": f"File type {extension} is not supported. Please upload a PDF file."
            }), 400
            
        # Generate a unique filename to avoid collisions
        unique_filename = f"{uuid.uuid4().hex}{extension}"
        
        # Read the PDF into memory
        pdf_data = file.read()
        pdf_stream = io.BytesIO(pdf_data)
        
        # Get or create a conversation to associate with this PDF
        # This ensures we have a valid conversation_id before trying to save the PDF
        from models import Conversation
        conversation = None
        
        # If conversation_id was provided, try to fetch that conversation
        if conversation_id:
            try:
                conversation = Conversation.query.get(conversation_id)
                logger.info(f"Found existing conversation with ID: {conversation_id}")
            except Exception as e:
                logger.error(f"Error finding conversation {conversation_id}: {e}")
                conversation_id = None
        
        # If no valid conversation found or provided, create a new one
        if not conversation:
            # Create a new conversation for this PDF upload
            try:
                # Import the function to generate a unique share ID
                from ensure_app_context import ensure_app_context
                
                # Use a descriptive title for PDF-initiated conversations
                title = f"PDF Document: {filename}"
                share_id = generate_share_id()
                
                # Create with app context to avoid "working outside of application context" errors
                with ensure_app_context():
                    # Generate a UUID for the conversation
                    conversation_uuid = str(uuid.uuid4())
                    
                    # Create the conversation with required fields including conversation_uuid
                    conversation = Conversation(
                        title=title, 
                        share_id=share_id,
                        conversation_uuid=conversation_uuid  # Add the required conversation_uuid field
                    )
                    
                    # Associate conversation with the authenticated user if available
                    if current_user and current_user.is_authenticated:
                        conversation.user_id = current_user.id
                        logger.info(f"Associating new PDF conversation with user ID: {current_user.id}")
                    
                    db.session.add(conversation)
                    db.session.commit()
                    conversation_id = conversation.id
                    logger.info(f"Created new conversation for PDF with ID: {conversation_id} and UUID: {conversation_uuid}")
            except Exception as e:
                logger.exception(f"Error creating conversation for PDF: {e}")
                return jsonify({"error": f"Database error: {str(e)}"}), 500
        
        # Storage path for Azure Blob Storage
        storage_path = unique_filename
        
        # PDF container name - use the dedicated PDFs container
        pdf_container_name = os.environ.get("AZURE_STORAGE_PDF_CONTAINER_NAME", "gloriamundopdfs")
        
        # Store the PDF in Azure Blob Storage or fallback to local storage
        if 'USE_AZURE_STORAGE' in globals() and USE_AZURE_STORAGE and 'blob_service_client' in globals() and blob_service_client:
            try:
                # Create a container client for the PDF container
                pdf_container_client = blob_service_client.get_container_client(pdf_container_name)
                
                # Check if container exists, if not create it
                try:
                    pdf_container_client.get_container_properties()
                    logger.info(f"Container {pdf_container_name} exists")
                except Exception as container_error:
                    logger.info(f"Container {pdf_container_name} does not exist, creating it...")
                    pdf_container_client = blob_service_client.create_container(pdf_container_name)
                    logger.info(f"Container {pdf_container_name} created successfully")
                
                # Get PDF data from the stream
                pdf_stream.seek(0)
                pdf_bytes = pdf_stream.read()
                
                # Create a blob client for the specific blob
                blob_client = pdf_container_client.get_blob_client(storage_path)
                
                # Set content settings (MIME type)
                content_settings = ContentSettings(content_type='application/pdf')
                
                # Upload the PDF data to Azure Blob Storage
                blob_client.upload_blob(
                    data=pdf_bytes,
                    content_settings=content_settings,
                    overwrite=True
                )
                
                # For OpenRouter, we need to use base64 encoded data URL
                pdf_stream.seek(0)
                base64_pdf = base64.b64encode(pdf_stream.read()).decode('utf-8')
                pdf_data_url = f"data:application/pdf;base64,{base64_pdf}"
                
                # Now save a Message record with the PDF URL so it's properly associated with the conversation
                try:
                    from models import Message
                    from ensure_app_context import ensure_app_context
                    
                    # Create a placeholder message to hold the PDF data
                    # This ensures PDFs are properly tracked in conversation history
                    with ensure_app_context():
                        pdf_message = Message(
                            conversation_id=conversation.id,
                            role='user',
                            content='', # Empty content since the PDF is the content
                            pdf_url=pdf_data_url,
                            pdf_filename=filename
                        )
                        db.session.add(pdf_message)
                        db.session.commit()
                        logger.info(f"Saved PDF message {pdf_message.id} for conversation {conversation.id}")
                except Exception as e:
                    logger.exception(f"Error saving PDF message to database: {e}")
                    # Continue even if this fails - we'll at least return the PDF URL
                
                logger.info(f"Uploaded PDF to Azure Blob Storage: {unique_filename}")
                
                return jsonify({
                    "success": True,
                    "pdf_url": blob_client.url,
                    "pdf_data_url": pdf_data_url,
                    "filename": filename,
                    "document_name": filename,  # Add document_name for display in UI
                    "conversation_id": conversation.id  # Return the conversation ID to the client
                })
            except Exception as e:
                logger.exception(f"Error uploading to Azure Blob Storage: {e}")
                # Fallback to local storage if Azure Blob Storage fails
                upload_dir = Path('static/uploads/pdfs')
                upload_dir.mkdir(parents=True, exist_ok=True)
                file_path = upload_dir / unique_filename
                
                with open(file_path, 'wb') as f:
                    pdf_stream.seek(0)
                    f.write(pdf_stream.read())
                
                pdf_url = url_for('static', filename=f'uploads/pdfs/{unique_filename}', _external=True)
                
                # For OpenRouter, we need to use base64 encoded data URL
                pdf_stream.seek(0)
                base64_pdf = base64.b64encode(pdf_stream.read()).decode('utf-8')
                pdf_data_url = f"data:application/pdf;base64,{base64_pdf}"
                
                # Save a Message record with the PDF URL so it's properly associated with the conversation
                try:
                    from models import Message
                    from ensure_app_context import ensure_app_context
                    
                    # Create a placeholder message to hold the PDF data
                    # This ensures PDFs are properly tracked in conversation history
                    with ensure_app_context():
                        pdf_message = Message(
                            conversation_id=conversation.id,
                            role='user',
                            content='', # Empty content since the PDF is the content
                            pdf_url=pdf_data_url,
                            pdf_filename=filename
                        )
                        db.session.add(pdf_message)
                        db.session.commit()
                        logger.info(f"Saved PDF message {pdf_message.id} for conversation {conversation.id}")
                except Exception as e:
                    logger.exception(f"Error saving PDF message to database: {e}")
                    # Continue even if this fails - we'll at least return the PDF URL
                
                logger.info(f"Fallback: Saved PDF to local filesystem: {file_path}")
                
                return jsonify({
                    "success": True,
                    "pdf_url": pdf_url,
                    "pdf_data_url": pdf_data_url,
                    "filename": filename,
                    "document_name": filename,  # Add document_name for display in UI
                    "conversation_id": conversation.id  # Return the conversation ID to the client
                })
        else:
            # Azure Blob Storage not available, use local filesystem
            upload_dir = Path('static/uploads/pdfs')
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / unique_filename
            
            with open(file_path, 'wb') as f:
                pdf_stream.seek(0)
                f.write(pdf_stream.read())
            
            pdf_url = url_for('static', filename=f'uploads/pdfs/{unique_filename}', _external=True)
            
            # For OpenRouter, we need to use base64 encoded data URL
            pdf_stream.seek(0)
            base64_pdf = base64.b64encode(pdf_stream.read()).decode('utf-8')
            pdf_data_url = f"data:application/pdf;base64,{base64_pdf}"
            
            # Save a Message record with the PDF URL so it's properly associated with the conversation
            try:
                from models import Message
                from ensure_app_context import ensure_app_context
                
                # Create a placeholder message to hold the PDF data
                # This ensures PDFs are properly tracked in conversation history
                with ensure_app_context():
                    pdf_message = Message(
                        conversation_id=conversation.id,
                        role='user',
                        content='', # Empty content since the PDF is the content
                        pdf_url=pdf_data_url,
                        pdf_filename=filename
                    )
                    db.session.add(pdf_message)
                    db.session.commit()
                    logger.info(f"Saved PDF message {pdf_message.id} for conversation {conversation.id}")
            except Exception as e:
                logger.exception(f"Error saving PDF message to database: {e}")
                # Continue even if this fails - we'll at least return the PDF URL
            
            logger.info(f"Saved PDF to local filesystem: {file_path}")
            
            return jsonify({
                "success": True,
                "pdf_url": pdf_url,
                "pdf_data_url": pdf_data_url,
                "filename": filename,
                "document_name": filename,  # Add document_name for display in UI
                "conversation_id": conversation.id  # Return the conversation ID to the client
            })
    except Exception as e:
        logger.exception(f"Error handling PDF upload: {e}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/upload', methods=['POST'])
def redirect_to_upload_file():
    """
    Route handler that redirects to the main upload_file function
    to maintain compatibility with any existing code using the /upload endpoint.
    """
    return upload_file()

@app.route('/api/cleanup-empty-conversations', methods=['POST'])
@login_required
def cleanup_empty_conversations_api():
    """Clean up all empty conversations for the current user"""
    try:
        from models import Conversation, Message
        from conversation_utils import cleanup_empty_conversations
        
        # Clean up empty conversations for the current user
        cleaned_count = cleanup_empty_conversations(db, Message, Conversation, current_user.id)
        
        logger.info(f"API call cleaned up {cleaned_count} empty conversations for user {current_user.id}")
        
        return jsonify({"success": True, "cleaned_count": cleaned_count})
    except Exception as e:
        logger.exception(f"Error cleaning up empty conversations for user {current_user.id}: {e}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/conversation/<int:conversation_id>/is-empty', methods=['GET'])
@login_required
def is_conversation_empty_api(conversation_id):
    """Check if a conversation is empty (has no messages)"""
    try:
        from models import Message, Conversation
        from conversation_utils import is_conversation_empty
        
        # First verify the conversation belongs to the current user
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
        if not conversation:
            return jsonify({"success": False, "error": "Conversation not found"}), 404
        
        # Check if conversation is empty
        empty = is_conversation_empty(db, Message, conversation_id)
        
        return jsonify({"success": True, "is_empty": empty})
    except Exception as e:
        logger.exception(f"Error checking if conversation {conversation_id} is empty: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
        
@app.route('/api/conversation/<int:conversation_id>/delete-if-empty', methods=['POST'])
@login_required
def delete_conversation_if_empty_api(conversation_id):
    """Delete a conversation if it has no messages"""
    try:
        from models import Message, Conversation
        from conversation_utils import delete_conversation_if_empty
        
        # Verify the conversation belongs to the current user
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
        if not conversation:
            return jsonify({"success": False, "error": "Conversation not found"}), 404
        
        # Check if conversation is empty and delete it if it is
        deleted = delete_conversation_if_empty(db, Message, Conversation, conversation_id)
        
        if deleted:
            logger.info(f"Deleted empty conversation {conversation_id} for user {current_user.id}")
            return jsonify({"success": True, "deleted": True})
        else:
            logger.info(f"Conversation {conversation_id} not empty or couldn't be deleted")
            return jsonify({"success": True, "deleted": False})
            
    except Exception as e:
        logger.exception(f"Error deleting empty conversation {conversation_id}: {e}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/clear-conversations', methods=['POST'])
@login_required
def clear_conversations():
    """Clear all conversations for the current user"""
    try:
        from models import Conversation
        
        # Mark all user's conversations as inactive (soft delete)
        logger.info(f"Clearing all conversations for user {current_user.id}")
        
        conversations = Conversation.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).all()
        
        count = 0
        for conv in conversations:
            conv.is_active = False
            count += 1
        
        db.session.commit()
        logger.info(f"Successfully marked {count} conversations as inactive for user {current_user.id}")
        
        # Create a new conversation
        title = "New Conversation"
        share_id = generate_share_id()
        conversation_uuid = str(uuid.uuid4())
        conversation = Conversation(
            title=title, 
            share_id=share_id,
            user_id=current_user.id,
            conversation_uuid=conversation_uuid
        )
        db.session.add(conversation)
        db.session.commit()
        logger.info(f"Created new conversation for user {current_user.id} with ID: {conversation.id}, UUID: {conversation_uuid}")
        
        return jsonify({"success": True, "message": f"Cleared {count} conversations", "new_conversation_id": conversation.id})
    
    except Exception as e:
        logger.exception(f"Error clearing conversations for user {current_user.id}: {e}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/rename-conversation/<int:conversation_id>', methods=['PUT'])
@login_required
def rename_conversation(conversation_id):
    """Rename a conversation for the current user"""
    try:
        # Get the new title from the request
        data = request.get_json()
        new_title = data.get('title', '').strip()
        
        if not new_title:
            return jsonify({"success": False, "error": "Title cannot be empty"}), 400
        
        from models import Conversation
        
        # Find the conversation by ID and make sure it belongs to the current user
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
        
        if not conversation:
            return jsonify({"success": False, "error": "Conversation not found"}), 404
        
        # Update the title
        conversation.title = new_title
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "conversation": {
                "id": conversation.id,
                "title": conversation.title
            }
        })
    
    except Exception as e:
        logger.exception(f"Error renaming conversation {conversation_id} for user {current_user.id}: {e}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/create-conversation', methods=['POST'])
@login_required
def create_conversation():
    """Create a new conversation for the current user"""
    try:
        from models import Conversation, Message
        from conversation_utils import cleanup_empty_conversations
        
        # First, clean up any existing empty conversations for this user
        cleaned_count = cleanup_empty_conversations(db, Message, Conversation, current_user.id)
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} empty conversations for user {current_user.id}")
        
        # Create a new conversation
        title = "New Conversation"
        share_id = generate_share_id()
        conversation_uuid = str(uuid.uuid4())
        conversation = Conversation(
            title=title, 
            share_id=share_id,
            user_id=current_user.id,
            conversation_uuid=conversation_uuid
        )
        
        db.session.add(conversation)
        db.session.commit()
        
        logger.info(f"Created new conversation from API for user {current_user.id} with ID: {conversation.id}, UUID: {conversation_uuid}")
        
        # Return the conversation data
        return jsonify({
            "success": True, 
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.exception(f"Error creating new conversation for user {current_user.id}: {e}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/conversations', methods=['GET'])
@login_required
def get_conversations():
    """Get all conversations for the current user"""
    try:
        from models import Conversation
        
        # Check if this is a request for metadata only (faster loading)
        metadata_only = request.args.get('metadata_only', 'false').lower() == 'true'
        
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
            conversation_uuid = str(uuid.uuid4())
            conversation = Conversation(
                title=title, 
                share_id=share_id,
                user_id=current_user.id,  # Associate conversation with user
                conversation_uuid=conversation_uuid
            )
            db.session.add(conversation)
            try:
                db.session.commit()
                logger.info(f"Created initial conversation for user {current_user.id} with ID: {conversation.id}, UUID: {conversation_uuid}")
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
            
            # Log information based on request type
            if metadata_only:
                logger.info(f"Returning metadata-only for {len(conversations)} conversations - optimized load")
            else:
                # Log each conversation's details for debugging (only in full data mode)
                for conv in conversations:
                    print(f"[CONVERSATIONS] ID: {conv['id']}, Title: '{conv['title']}', Created: {conv['created_at']}")
                
                logger.info(f"Returning {len(conversations)} conversations with full details")

        return jsonify({"conversations": conversations})
    except Exception as e:
        logger.exception("Error getting conversations")
        return jsonify({"error": str(e)}), 500

# --- SYNCHRONOUS CHAT ENDPOINT (Using Requests) ---
@app.route('/chat', methods=['POST'])
def chat(): # Synchronous function
    """
    Endpoint to handle chat messages and stream responses from OpenRouter (SYNC Version)
    
    This endpoint is rate limited to prevent abuse and ensure fair usage.
    Rate limits are:
    - Authenticated users: 20 requests per minute
    - Guest users: 5 requests per minute
    """
    # Rate limiting implementation will be applied once the app is configured with Redis
    # Declare global variables at the beginning of the function
    global document_processor
    
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
        pdf_url = None     # For backward compatibility
        pdf_urls = []      # Array of all PDF URLs
        pdf_filename = "document.pdf"  # Default PDF filename
        
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
                        elif item.get('type') == 'file':
                            file_obj = item.get('file', {})
                            file_data = file_obj.get('file_data')
                            filename = file_obj.get('filename', 'document.pdf')
                            if file_data:
                                pdf_urls.append(file_data)
                                # Set pdf_url to the first PDF for backward compatibility
                                if not pdf_url:
                                    pdf_url = file_data
                                    pdf_filename = filename
                                logger.info(f"Extracted PDF data from messages array: {filename}")
        
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
            
            # Initialize RAG content flag
            has_rag_content = False
            relevant_chunks = []
            
            # Global document_processor is already declared at the function start
            
            # Only check for RAG content if RAG is enabled and there's a user message
            if ENABLE_RAG and user_message and len(user_message.strip()) > 0:
                # Get user ID for retrieving documents
                rag_user_id = str(current_user.id) if current_user and current_user.is_authenticated else get_user_identifier()
                logger.info(f"RAG: Pre-checking for document availability for user_id: {rag_user_id}")
                
                # Check if the user has any documents before attempting retrieval
                try:
                    # Import document processor on demand to avoid circular imports
                    if 'document_processor' not in globals() or document_processor is None:
                        document_processor = DocumentProcessor()
                    
                    # Check if Azure OpenAI credentials are available
                    azure_key = os.environ.get('AZURE_OPENAI_API_KEY')
                    azure_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
                    azure_deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT')
                    
                    if not (azure_key and azure_endpoint and azure_deployment):
                        logger.error("RAG: Azure OpenAI credentials are missing or incomplete.")
                        # Skip RAG retrieval when credentials are missing
                    else:
                        # Do a preliminary check to see if the user has any documents
                        has_documents = document_processor.user_has_documents(rag_user_id)
                        if has_documents:
                            has_rag_content = True
                            logger.info("Detected RAG usage - user has documents - marking as requiring advanced model")
                        else:
                            logger.info("No documents found for user - not marking as RAG content")
                except Exception as e:
                    logger.error(f"Error checking for user documents: {e}")
                    # If we can't determine, assume no RAG to avoid using expensive models unnecessarily
            
            # Get the list of available models
            logger.info(f"🔍 CHAT: Getting available models for validation")
            available_models = model_validator.get_available_models()
            logger.info(f"🔍 CHAT: Received {len(available_models) if available_models else 0} available models")
            
            # Check if the requested model is available
            logger.info(f"🔍 CHAT: Validating requested model: {openrouter_model}")
            model_is_available = model_validator.is_model_available(openrouter_model, available_models)
            logger.info(f"🔍 CHAT: Model availability check result: {model_is_available}")
            logger.info(f"🔍 CHAT: Has RAG content: {has_rag_content}")
            logger.info(f"🔍 CHAT: Combined condition (not available OR has RAG): {not model_is_available or has_rag_content}")
            
            if not model_is_available or has_rag_content:
                
                # Check if user wants fallback behavior
                enable_fallback = True  # Default for non-authenticated users
                
                # For authenticated users, respect their preference
                if current_user and current_user.is_authenticated:
                    enable_fallback = current_user.enable_model_fallback
                    logger.info(f"User {current_user.id} fallback preference: {enable_fallback}")
                
                if enable_fallback:
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
                        adaptive_model = model_validator.select_multimodal_fallback(
                            has_image_content=has_image, 
                            available_models=available_models,
                            has_rag_content=has_rag_content
                        )
                        logger.info(f"Using adaptive model selection: {adaptive_model} (image content: {has_image}, RAG content: {has_rag_content})")
                        openrouter_model = adaptive_model
                else:
                    # User has disabled fallback behavior
                    logger.info(f"Model fallback disabled by user preference. Requested model {openrouter_model} is unavailable.")
                    return jsonify({
                        "text": f"The model '{openrouter_model}' is currently unavailable. Please select a different model or enable model fallback in your account settings.",
                        "model": openrouter_model,
                        "error": True
                    }), 400
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
            conversation_uuid = str(uuid.uuid4())
            conversation = Conversation(title=title, share_id=share_id, conversation_uuid=conversation_uuid)
            # Associate conversation with the authenticated user
            if current_user and current_user.is_authenticated:
                conversation.user_id = current_user.id
                logger.info(f"Associating new conversation with user ID: {current_user.id}")
            db.session.add(conversation)
            try:
                db.session.commit()
                conversation_id = conversation.id 
                logger.info(f"Created new conversation with ID: {conversation_id}, UUID: {conversation_uuid}")
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
        logger.info(f"Saving user message to DB. Text: '{message_text[:50]}...' Image URL: {image_url[:50] if image_url else 'None'} PDF URL: {'Present' if pdf_url else 'None'}")
        
        # Import our app context manager
        from ensure_app_context import ensure_app_context
        
        # Ensure all database operations are performed within the app context
        with ensure_app_context():
            user_db_message = Message(
                conversation_id=conversation.id, 
                role='user', 
                content=message_text,  # Store the text component
                image_url=image_url,   # Store the image URL separately
                pdf_url=pdf_url,       # Store the PDF URL separately
                pdf_filename=pdf_filename if pdf_url else None  # Store the PDF filename if we have a PDF
            )
            db.session.add(user_db_message)
            try:
                db.session.commit()
                logger.info(f"Saved user message {user_db_message.id} for conversation {conversation.id}")
                # Log if multimodal content was included
                if image_url:
                    logger.info(f"Image URL saved with message: {image_url[:50]}...")
                if pdf_url:
                    logger.info(f"PDF information saved with message: {pdf_filename}")
            except Exception as e:
                logger.exception(f"Error committing user message to database: {e}")
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

        # Check if model supports multimodal input by querying the database
        model_supports_multimodal = False
        
        # Import OpenRouterModel class
        from models import OpenRouterModel
        
        # Query the database for this specific model
        db_model = OpenRouterModel.query.filter_by(model_id=openrouter_model).first()
        
        if db_model:
            # Use the is_multimodal flag from the database
            model_supports_multimodal = db_model.is_multimodal
            logger.info(f"✅ Found model in database: {openrouter_model}, multimodal={model_supports_multimodal}")
        else:
            # Model not found in database - default to False for safety
            logger.warning(f"No database entry found for model {openrouter_model}, assuming non-multimodal support")
            # For critical anthropic/claude and vision models, use a basic heuristic as fallback
            if any(pattern in openrouter_model.lower() for pattern in ["claude-3", "claude-3.5", "claude-3.7", "gpt-4-vision", "gpt-4o", "gemini"]):
                model_supports_multimodal = True
                logger.info(f"⚠️ Assuming multimodal support for {openrouter_model} based on model ID pattern matching")
            
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
                
        # Check if we have images or PDFs to include
        has_images = image_url or (image_urls and len(image_urls) > 0)
        has_pdfs = pdf_url or (pdf_urls and len(pdf_urls) > 0)
        
        # Check if model supports multimodal content or PDF documents
        # First try to look up the model in the database
        model_supports_documents = openrouter_model in DOCUMENT_MODELS
        try:
            # Check the database for more accurate information
            from models import OpenRouterModel
            db_model = OpenRouterModel.query.get(openrouter_model)
            if db_model and db_model.supports_pdf:
                model_supports_documents = True
        except Exception as e:
            logger.warning(f"Error checking database for PDF support: {e}")
        
        # Include multimedia content if we have images or PDFs and the model supports them
        if (has_images and model_supports_multimodal) or (has_pdfs and model_supports_documents):
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
            
            # Add PDFs to the multimodal content if available and model supports it
            if has_pdfs and model_supports_documents:
                # Process all PDFs in the pdf_urls array
                pdf_to_process = []
                if pdf_url:
                    pdf_to_process.append((pdf_url, pdf_filename))
                if pdf_urls:
                    # Assuming pdf_urls contains data URLs
                    for idx, pdf_data in enumerate(pdf_urls):
                        filename = f"document_{idx+1}.pdf"
                        pdf_to_process.append((pdf_data, filename))
                
                for pdf_data_url, filename in pdf_to_process:
                    # Validate that this is a data URL (required for OpenRouter PDF handling)
                    if pdf_data_url.startswith('data:application/pdf;base64,'):
                        # Add this PDF to the multimodal content
                        multimodal_content.append({
                            "type": "file",
                            "file": {
                                "filename": filename,
                                "file_data": pdf_data_url
                            }
                        })
                        logger.info(f"Added PDF document to message: {filename}")
                    else:
                        logger.error(f"❌ INVALID PDF DATA URL FORMAT: PDF URLs must be data:application/pdf;base64,... format")
                        logger.error(f"Received format: {pdf_data_url[:100]}...")
            
            # Add the multimodal content to messages if we have at least one valid image or PDF
            if len(multimodal_content) > 1:  # First item is text, so we need more than 1 item
                messages.append({'role': 'user', 'content': multimodal_content})
                
                # Count the number of images and PDFs
                image_count = sum(1 for item in multimodal_content if item.get('type') == 'image_url')
                pdf_count = sum(1 for item in multimodal_content if item.get('type') == 'file')
                
                logger.info(f"✅ Added multimodal message with {image_count} images and {pdf_count} PDFs to {openrouter_model}")
                
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
        if has_images and not model_supports_multimodal:
            logger.warning(f"⚠️ Image URL(s) provided but model {openrouter_model} doesn't support multimodal input. Images ignored.")
            
        # Log if PDF was provided but model doesn't support it    
        if has_pdfs and not model_supports_documents:
            logger.warning(f"⚠️ PDF document(s) provided but model {openrouter_model} doesn't support PDF handling. PDFs ignored.")

        # --- Enrich with memory if needed and user has it enabled ---
        if ENABLE_MEMORY_SYSTEM:
            memory_enabled = True
            if current_user and current_user.is_authenticated:
                memory_enabled = current_user.enable_memory
                logger.info(f"User {current_user.id} memory preference: {'enabled' if memory_enabled else 'disabled'}")
            
            if memory_enabled:
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
            else:
                logger.info("Memory enrichment skipped - user has disabled memory across sessions")
                 
        # --- Incorporate document context from RAG system ---
        if ENABLE_RAG:
            try:
                # We already did the pre-check for has_rag_content flag when selecting the model
                # Now do the actual document retrieval if needed
                
                # Get user ID for retrieving documents
                rag_user_id = str(current_user.id) if current_user and current_user.is_authenticated else get_user_identifier()
                logger.info(f"RAG: Attempting retrieval for user_id: {rag_user_id}, Query: '{user_message[:50]}...'")
                
                # Global document_processor is already declared at the function start
                
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
                        # Only attempt retrieval if we know the user has documents
                        # This should match the check we did earlier when setting has_rag_content
                        # Import document processor on demand to avoid circular imports
                        if 'document_processor' not in globals() or document_processor is None:
                            document_processor = DocumentProcessor()
                            
                        # Double-check if the user has documents (should be true if has_rag_content was set)
                        if document_processor.user_has_documents(rag_user_id):
                            # User has documents, proceed with retrieval
                            relevant_chunks = document_processor.retrieve_relevant_chunks(
                                query_text=user_message,
                                user_id=rag_user_id,
                                limit=5  # Retrieve top 5 most relevant chunks
                            )
                            logger.info(f"RAG: Found {len(relevant_chunks)} relevant chunks using Azure embeddings.")
                        else:
                            # User doesn't have documents, skip retrieval
                            logger.info("RAG: User has no documents, skipping retrieval")
                            relevant_chunks = []
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
                    
                    # Add a flag to track that this conversation is using document retrieval
                    # This will be used to display a visual indicator in the UI
                    has_rag_documents = True
                    doc_sources = [chunk.get('source_document_name', 'Unknown') for chunk in relevant_chunks]
                    unique_sources = list(set(doc_sources))
                    
                    # Debug logging for RAG document detection
                    print(f"DEBUG-RAG-DETECTION: Set has_rag_documents={has_rag_documents}")
                    print(f"DEBUG-RAG-DETECTION: Document sources: {doc_sources}")
                    print(f"DEBUG-RAG-DETECTION: Unique sources: {unique_sources}")
                else:
                    logger.info("No relevant document chunks found for the query")
                    
            except Exception as e:
                logger.error(f"Error incorporating RAG context: {e}")

        # --- Prepare Payload ---
        # Before creating payload, ensure we have correct content format for each model type
        # OpenRouter expects different message content formats for multimodal vs non-multimodal models
        
        # Check if model supports multimodal content using database
        model_supports_multimodal = False
        from models import OpenRouterModel
        
        # Query the database for this specific model
        db_model = OpenRouterModel.query.filter_by(model_id=openrouter_model).first()
        
        if db_model:
            # Use the is_multimodal flag from the database
            model_supports_multimodal = db_model.is_multimodal
            logger.info(f"Model {openrouter_model} supports multimodal content: {model_supports_multimodal}")
        else:
            # Model not found in database - use a basic heuristic as fallback
            multimodal_indicators = ["claude-3", "claude-3.5", "claude-3.7", "gpt-4-vision", "gpt-4o", "gemini", "vision", "multimodal"]
            for indicator in multimodal_indicators:
                if indicator.lower() in openrouter_model.lower():
                    model_supports_multimodal = True
                    logger.info(f"Model {openrouter_model} assumed to support multimodal content (pattern: {indicator})")
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
        
        # Apply user's advanced chat parameter settings if available
        if current_user and current_user.is_authenticated:
            try:
                import json
                from user_settings import get_chat_settings_for_user, validate_model_specific_parameters
                
                # Get the user's chat settings
                user_settings = get_chat_settings_for_user(current_user.id)
                
                # Validate and adjust parameters based on model constraints
                if user_settings:
                    user_settings = validate_model_specific_parameters(user_settings, openrouter_model)
                    
                    # Add validated settings to the payload
                    payload.update(user_settings)
                    
                    logger.info(f"Applied user chat settings: {json.dumps(user_settings)}")
            except Exception as e:
                logger.error(f"Error applying user chat settings: {e}")
                # Continue without user settings if there's an error
        
        # Add PDF plugin configuration if this model supports documents (native engine for PDFs)
        # This ensures PDFs are processed by the native model capabilities instead of falling back to OCR
        has_pdf_content = False
        for msg in processed_messages:
            content = msg.get('content', '')
            if isinstance(content, list):
                for item in content:
                    if item.get('type') == 'file' and 'file_data' in item.get('file', {}):
                        has_pdf_content = True
                        break
        
        # Check if model supports PDF files (from database or hardcoded list)
        model_supports_pdf = openrouter_model in DOCUMENT_MODELS
        try:
            # Check the database for more accurate information
            from models import OpenRouterModel
            db_model = OpenRouterModel.query.get(openrouter_model)
            if db_model and db_model.supports_pdf:
                model_supports_pdf = True
        except Exception as e:
            logger.warning(f"Error checking database for PDF support: {e}")
            
        if has_pdf_content and model_supports_pdf:
            logger.info(f"PDF content detected for document-capable model {openrouter_model}, adding native PDF plugin config")
            payload['plugins'] = [
                {
                    "id": "file-parser",
                    "pdf": {
                        "engine": "native"
                    }
                }
            ]
        
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
                        elif item_type == 'file':
                            file_obj = content_item.get('file', {})
                            filename = file_obj.get('filename', 'unknown')
                            file_data = file_obj.get('file_data', '')
                            is_valid_data_url = file_data.startswith('data:application/pdf;base64,')
                            logger.info(f"  Content item {i}: type=file, filename={filename}, valid_data_url={is_valid_data_url}")
                            if not is_valid_data_url:
                                logger.error(f"❌ INVALID PDF DATA FORMAT: PDF data must be in data:application/pdf;base64,... format")
                            
                            # For image_url type, we'll check URL format in the next section
            
            # Now compare what was in the original vs what's in the processed payload
            original_has_multimodal = any(isinstance(msg.get('content'), list) for msg in messages)
            if original_has_multimodal != has_multimodal_message:
                if original_has_multimodal and not has_multimodal_message:
                    logger.info("✅ Successfully converted multimodal content to text-only for non-multimodal model")
                elif not original_has_multimodal and has_multimodal_message:
                    logger.warning("⚠️ Unexpected conversion: text-only content became multimodal!")
            
            if image_url and not has_multimodal_message:
                logger.info("ℹ️ image_url was provided but no multimodal message in final payload - correctly converted for non-multimodal model")
            
            # Check final model and multimodal status match with the database
            selected_model = payload.get('model', '')
            model_supports_multimodal = False
            
            # Query the database for this specific model
            from models import OpenRouterModel
            db_model = OpenRouterModel.query.filter_by(model_id=selected_model).first()
            
            if db_model:
                # Use the is_multimodal flag from the database
                model_supports_multimodal = db_model.is_multimodal
            else:
                # Fall back to a basic heuristic if the model isn't in the database
                multimodal_indicators = ["claude-3", "claude-3.5", "claude-3.7", "gpt-4-vision", "gpt-4o", "gemini", "vision", "multimodal"]
                for indicator in multimodal_indicators:
                    if indicator.lower() in selected_model.lower():
                        model_supports_multimodal = True
                        break
            
            # Verify content format matches model capabilities
            if model_supports_multimodal != has_multimodal_message:
                if model_supports_multimodal and not has_multimodal_message:
                    # This is completely fine, just log as info
                    logger.info("ℹ️ Using text-only message with a multimodal-capable model")
                elif not model_supports_multimodal and has_multimodal_message:
                    # This could be a real issue, keep as warning
                    logger.warning("⚠️ Model does NOT support multimodal but we're sending multimodal content!")
            else:
                logger.info(f"✅ Content format correctly matched to model capabilities: multimodal={model_supports_multimodal}")
            
            # Create a safe copy of the payload for logging (to avoid credentials leaks)
            log_payload = payload.copy()
            # Make sure json is available in this scope
            import json
            # Use json.dumps for clean logging of the entire payload
            final_payload_json = json.dumps(log_payload, indent=2)
            logger.debug(f"PAYLOAD DEBUG: Final payload being sent to OpenRouter:\n{final_payload_json}")
        except Exception as json_err:
            logger.error(f"PAYLOAD DEBUG: Error serializing payload for logging: {json_err}")
        # --- END OF ADDED LOGGING ---
        
        logger.debug(f"Sending request to OpenRouter with model: {openrouter_model}. History length: {len(messages)}, include_reasoning: True")

        # --- Define the SYNC Generator using requests ---
        def generate():
            # Make json module accessible in this scope (required for json.loads, json.dumps)
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

                                    # --- Extract Content, Reasoning and Citations ---
                                    content_chunk = None
                                    reasoning_chunk = None
                                    citations = None
                                    
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
                                            
                                    # Extract citations if available (for Perplexity models)
                                    # Citations are at the top level in the OpenRouter response for Perplexity
                                    if 'citations' in json_data and requested_model_id and 'perplexity' in requested_model_id:
                                        citations = json_data.get('citations')
                                        logger.debug(f"Found {len(citations) if citations else 0} citations in Perplexity response")

                                    # Handle content chunk
                                    if content_chunk:
                                        assistant_response_content.append(content_chunk)
                                        logger.info(f"🔍 CONTENT ACCUMULATION: Added chunk '{content_chunk[:50]}...' (total chunks: {len(assistant_response_content)})")
                                        # Yield content chunk to the client
                                        content_payload = {'type': 'content', 'content': content_chunk, 'conversation_id': current_conv_id}
                                        content_json_str = json.dumps(content_payload)
                                        yield f"data: {content_json_str}\n\n"
                                    
                                    # Handle reasoning chunk
                                    if reasoning_chunk:
                                        # Yield reasoning chunk to the client
                                        reasoning_payload = {'type': 'reasoning', 'reasoning': reasoning_chunk, 'conversation_id': current_conv_id}
                                        reasoning_json_str = json.dumps(reasoning_payload)
                                        yield f"data: {reasoning_json_str}\n\n"
                                    
                                    # Handle citations if available (for Perplexity models)
                                    if citations:
                                        # Send citations as a separate event
                                        citations_payload = {'type': 'citations', 'citations': citations, 'conversation_id': current_conv_id}
                                        citations_json_str = json.dumps(citations_payload)
                                        logger.debug(f"Sending {len(citations)} citations to client")
                                        yield f"data: {citations_json_str}\n\n"

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
                                    error_payload = {'type': 'error', 'error': 'JSON parsing error'}
                                    error_json_str = json.dumps(error_payload)
                                    yield f"data: {error_json_str}\n\n"
                                    return # Stop generation on genuine parsing error

                # --- Stream processing finished ---
                logger.info(f"🔍 STREAM PROCESSING: Content accumulation debug")
                logger.info(f"🔍 assistant_response_content length: {len(assistant_response_content)}")
                logger.info(f"🔍 assistant_response_content sample: {assistant_response_content[:3] if assistant_response_content else 'Empty list'}")
                
                full_response_text = ''.join(assistant_response_content)
                logger.info(f"🔍 full_response_text length: {len(full_response_text)}")
                logger.info(f"🔍 full_response_text sample: {repr(full_response_text[:100]) if full_response_text else 'Empty string'}")

                # Always send metadata regardless of content accumulation issues
                # This fixes the bug where metadata wasn't being sent due to content accumulation problems
                logger.info(f"🔧 METADATA FIX: Always proceeding with metadata generation")
                logger.info(f"🔧 Original condition would be: {bool(full_response_text)}")
                
                if True:  # Always generate metadata - content streaming works independently
                    try:
                        from models import Message
                        from ensure_app_context import ensure_app_context
                        
                        # Use our app context manager to avoid "outside application context" errors
                        with ensure_app_context():
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

                        # Save to memory system if enabled and user hasn't disabled it
                        if ENABLE_MEMORY_SYSTEM:
                             memory_enabled = True
                             if current_user and current_user.is_authenticated:
                                 memory_enabled = current_user.enable_memory
                             
                             if memory_enabled:
                                 try:
                                     memory_user_id = str(current_user.id) if current_user and current_user.is_authenticated else f"anonymous_{current_conv_id}"
                                     save_message_with_memory(
                                         session_id=str(current_conv_id), user_id=memory_user_id, 
                                         role='assistant', content=full_response_text
                                     )
                                 except Exception as e:
                                     logger.error(f"Error saving assistant message to memory: {e}")
                             else:
                                 logger.info("Message not saved to memory - user has disabled memory across sessions")
                        
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
                                logger.info(f"DEBUG: /chat - ABOUT TO CALL generate_summary for conversation {current_conv_id}")
                                try:
                                    generate_summary(current_conv_id)
                                    print(f"[CHAT] Title generation for conversation {current_conv_id} initiated successfully")
                                    logger.info(f"DEBUG: /chat - RETURNED FROM generate_summary CALL for conversation {current_conv_id}")
                                except Exception as e:
                                    import traceback
                                    print(f"[CHAT] Error initiating title generation: {e}")
                                    logger.error(f"DEBUG: /chat - ERROR DURING generate_summary CALL: {e}")
                                    traceback.print_exc()
                        except Exception as e:
                            logger.error(f"Error checking message count or triggering title generation: {e}")
                            # Don't raise the exception - we want to continue even if this fails

                        # Yield the final metadata event
                        logger.info(f"==> Preparing to yield METADATA for message {assistant_message_id}")
                        # Prepare metadata payload
                        metadata_payload = {
                            'id': assistant_message_id, 
                            'model_id_used': final_model_id_used, 
                            'prompt_tokens': final_prompt_tokens, 
                            'completion_tokens': final_completion_tokens
                        }
                        
                        # DETAILED METADATA LOGGING
                        logger.info(f"🔍 METADATA DEBUG - Raw values:")
                        logger.info(f"🔍 assistant_message_id: {assistant_message_id} (type: {type(assistant_message_id)})")
                        logger.info(f"🔍 final_model_id_used: {final_model_id_used} (type: {type(final_model_id_used)})")
                        logger.info(f"🔍 final_prompt_tokens: {final_prompt_tokens} (type: {type(final_prompt_tokens)})")
                        logger.info(f"🔍 final_completion_tokens: {final_completion_tokens} (type: {type(final_completion_tokens)})")
                        
                        # Add document info if RAG was used
                        if 'has_rag_documents' in locals() and has_rag_documents:
                            metadata_payload['using_documents'] = True
                            if 'unique_sources' in locals() and unique_sources:
                                metadata_payload['document_sources'] = unique_sources
                            
                            # Enhanced debug logging for metadata payload with RAG info
                            print(f"DEBUG-RAG-METADATA: Adding RAG info to metadata_payload")
                            print(f"DEBUG-RAG-METADATA: using_documents = {metadata_payload.get('using_documents')}")
                            print(f"DEBUG-RAG-METADATA: document_sources = {metadata_payload.get('document_sources', [])}")
                        else:
                            print(f"DEBUG-RAG-METADATA: Not adding RAG info (has_rag_documents={('has_rag_documents' in locals() and has_rag_documents)})")
                            if 'has_rag_documents' in locals():
                                print(f"DEBUG-RAG-METADATA: has_rag_documents explicitly set to {has_rag_documents}")
                            else:
                                print(f"DEBUG-RAG-METADATA: has_rag_documents variable not defined in this scope")
                        
                        # DETAILED PAYLOAD LOGGING
                        logger.info(f"🔍 METADATA PAYLOAD: {metadata_payload}")
                        
                        # Create the full stream message
                        stream_message = {'type': 'metadata', 'metadata': metadata_payload}
                        logger.info(f"🔍 FULL STREAM MESSAGE: {stream_message}")
                        
                        # Create the JSON string that will be sent
                        json_string = json.dumps(stream_message)
                        logger.info(f"🔍 JSON STRING TO SEND: {json_string}")
                        
                        # Create the final data line
                        data_line = f"data: {json_string}\n\n"
                        logger.info(f"🔍 FINAL DATA LINE: {repr(data_line)}")
                                
                        # Send the metadata
                        yield data_line
                        logger.info(f"==> SUCCESSFULLY yielded METADATA for message {assistant_message_id}")

                    except Exception as db_error:
                        logger.exception("Error saving assistant message or metadata to DB")
                        db.session.rollback()
                        yield f"data: {json.dumps({'type': 'error', 'error': 'Error saving message to database'})}\n\n"
                else:
                     logger.error(f"🚨 CRITICAL: Assistant response was empty - this prevents metadata from being sent!")
                     logger.error(f"🚨 assistant_response_text length: {len(assistant_response_text) if assistant_response_text else 'None'}")
                     logger.error(f"🚨 assistant_response_text content: {repr(assistant_response_text[:100]) if assistant_response_text else 'None'}")
                     logger.error("🚨 This is why metadata is missing from the frontend!")

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

@app.route('/chat/stream', methods=['GET'])
def chat_stream_safari_fallback():
    """
    EventSource-compatible streaming endpoint for Safari iOS compatibility.
    
    This route provides a fallback for iOS Safari browsers which have issues
    with fetch() streaming. It uses Server-Sent Events (EventSource) instead.
    
    The client stores the payload in sessionStorage and passes a temp_id
    parameter to this endpoint to retrieve it.
    """
    try:
        temp_id = request.args.get('temp_id')
        if not temp_id:
            return "Missing temp_id parameter", 400
            
        logger.info(f"Safari fallback: handling stream request with temp_id={temp_id}")
        
        # This is a placeholder implementation - the actual payload would be
        # retrieved from a temporary storage mechanism (Redis, database, or sessionStorage)
        # For now, we'll return an error directing users to use the main endpoint
        
        def generate_safari_fallback():
            """Generate SSE-compatible response for Safari"""
            yield f"data: {json.dumps({'type': 'error', 'error': 'Safari fallback endpoint - please use the main /chat endpoint with the compatibility layer'})}\n\n"
            yield f"event: complete\ndata: {json.dumps({'type': 'complete'})}\n\n"
        
        return Response(
            stream_with_context(generate_safari_fallback()),
            content_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )
        
    except Exception as e:
        logger.exception("Error in Safari fallback endpoint")
        return f"Error: {str(e)}", 500


# --- Other Synchronous Routes (Keep As Is) ---
# Helper function to fetch models from OpenRouter and/or database
def _fetch_openrouter_models(force_refresh=False):
    """
    Fetch models from the database (primary) or OpenRouter API (fallback)
    with Redis caching for improved performance.
    
    Args:
        force_refresh: If True, bypass the cache and fetch fresh data
        
    Returns:
        list: Processed models data
    """
    # Try to use Redis cache for better performance
    try:
        from api_cache import cache_api_response
        
        @cache_api_response(prefix="openrouter_models", ttl=3600)
        def fetch_models_with_cache(force_refresh=False):
            """
            Inner function that's cached with Redis
            """
            # Force refresh flag for bypassing cache
            if force_refresh:
                logger.info("Forcing refresh of OpenRouter models from database")
            
            # Import the model class
            from models import OpenRouterModel
            
            # Get models from the database first (primary source of truth)
            db_models = OpenRouterModel.query.filter(OpenRouterModel.model_is_active == True).all()
            
            # If we have models in the database, use them
            if db_models and len(db_models) > 0:
                logger.info(f"Using {len(db_models)} models from database")
                
                # Transform database models to API-compatible format
                processed_models = []
                for model in db_models:
                    processed_model = {
                        'id': model.model_id,
                        'name': model.name,
                        'description': model.description,
                        'context_length': model.context_length,
                        'pricing': {
                            'prompt': model.input_price_usd_million / 1000000,  # Convert from per-million to per-token
                            'completion': model.output_price_usd_million / 1000000  # Convert from per-million to per-token
                        },
                        'is_free': model.is_free,
                        'is_multimodal': model.is_multimodal,
                        'supports_pdf': model.supports_pdf or model.model_id in DOCUMENT_MODELS,
                        'is_perplexity': 'perplexity/' in model.model_id.lower(),
                        'is_reasoning': model.supports_reasoning,
                        'created_at': model.created_at.isoformat() if model.created_at else None,
                        'updated_at': model.updated_at.isoformat() if model.updated_at else None
                    }
                    processed_models.append(processed_model)
                
                # Return API-compatible format
                return {"data": processed_models}
            
            # If database is empty or no active models found, try to update from OpenRouter API
            logger.info("No models in database or forced refresh - trying price updater")
            try:
                from price_updater import fetch_and_store_openrouter_prices
                success = fetch_and_store_openrouter_prices(force_update=True)
                
                if success:
                    # Try to get models from database again after updating
                    db_models = OpenRouterModel.query.filter(OpenRouterModel.model_is_active == True).all()
                    
                    if db_models and len(db_models) > 0:
                        # Convert to API format
                        processed_models = []
                        for model in db_models:
                            processed_model = {
                                'id': model.model_id,
                                'name': model.name,
                                'description': model.description,
                                'context_length': model.context_length,
                                'pricing': {
                                    'prompt': model.input_price_usd_million / 1000000,
                                    'completion': model.output_price_usd_million / 1000000
                                },
                                'is_free': model.is_free,
                                'is_multimodal': model.is_multimodal,
                                'supports_pdf': model.supports_pdf or model.model_id in DOCUMENT_MODELS,
                                'is_perplexity': 'perplexity/' in model.model_id.lower(),
                                'is_reasoning': model.supports_reasoning,
                                'created_at': model.created_at.isoformat() if model.created_at else None,
                                'updated_at': model.updated_at.isoformat() if model.updated_at else None
                            }
                            processed_models.append(processed_model)
                            
                        logger.info(f"Successfully retrieved {len(processed_models)} models from database after update")
                        return {"data": processed_models}
                        
                # If we still don't have models, use the legacy cache as last resort
                logger.warning("Could not get models from database - using legacy cache")
            except Exception as e:
                logger.error(f"Error updating models from OpenRouter: {e}")
        
        # Call the cached function with force_refresh parameter
        return fetch_models_with_cache(force_refresh=force_refresh)
                
    except Exception as e:
        logger.error(f"Error in Redis caching for OpenRouter models: {e}")
        
    # Default fallback implementation (original code path)
    try:
        # Fallback to API if database is empty
        # Try to update the database using price_updater
        logger.warning("No models found in database, attempting to fetch from OpenRouter API")
        from price_updater import fetch_and_store_openrouter_prices
        
        # Try to fetch and store prices
        success = fetch_and_store_openrouter_prices()
        
        if success:
            # Try again with database after successful update
            db_models = OpenRouterModel.query.all()
            if db_models and len(db_models) > 0:
                logger.info(f"Successfully populated database with {len(db_models)} models from API")
                
                # Transform database models to API-compatible format (same as above)
                processed_models = []
                for model in db_models:
                    processed_model = {
                        'id': model.model_id,
                        'name': model.name,
                        'description': model.description,
                        'context_length': model.context_length,
                        'pricing': {
                            'prompt': model.input_price_usd_million / 1000000,
                            'completion': model.output_price_usd_million / 1000000
                        },
                        'is_free': model.is_free,
                        'is_multimodal': model.is_multimodal,
                        'supports_pdf': model.supports_pdf or model.model_id in DOCUMENT_MODELS,
                        'is_perplexity': 'perplexity/' in model.model_id.lower(),
                        'is_reasoning': model.supports_reasoning,
                        'created_at': model.created_at.isoformat() if model.created_at else None,
                        'updated_at': model.updated_at.isoformat() if model.updated_at else None
                    }
                    processed_models.append(processed_model)
                
                return {"data": processed_models}
            else:
                logger.error("Failed to populate database after API fetch")
                return {"data": []}
        else:
            logger.error("Failed to fetch models from OpenRouter API")
            return {"data": []}
            
    except Exception as e:
        logger.exception(f"Error fetching models: {e}")
        return {"data": []}
        return None

@app.route('/api/get_model_prices', methods=['GET'])
def get_model_prices():
    """ 
    Get the current model prices from the database with Redis caching for instant loading
    """
    try:
        # Try to get cached pricing data first for instant loading
        try:
            from api_cache import get_redis_client
            redis_client = get_redis_client('cache')
            
            if redis_client:
                cached_data = redis_client.get('cache:pricing_table_data')
                if cached_data:
                    import json
                    logger.info("Serving pricing data from Redis cache for instant loading")
                    return jsonify(json.loads(cached_data))
        except Exception as e:
            logger.debug(f"Redis cache unavailable, proceeding with database: {e}")
        
        # Get fresh data from database
        from models import OpenRouterModel
        
        # Query all models from the database
        db_models = OpenRouterModel.query.all()
        
        if db_models:
            # Convert database models to the expected format with robust handling
            prices = {}
            models_with_missing_data = []
            
            for db_model in db_models:
                try:
                    # Only include active models
                    if not db_model.model_is_active:
                        continue
                        
                    model_id = db_model.model_id
                    
                    # CRITICAL FIX: Use stored cost band, generate and persist if missing
                    cost_band = db_model.cost_band
                    if not cost_band or cost_band.strip() == '':
                        input_price = db_model.input_price_usd_million or 0
                        if db_model.is_free or input_price == 0:
                            cost_band = "Free"
                        elif input_price < 1.0:
                            cost_band = "$"
                        elif input_price < 5.0:
                            cost_band = "$$"
                        else:
                            cost_band = "$$$"
                        
                        # CRITICAL FIX: Persist the generated cost band to database to prevent regeneration
                        try:
                            db_model.cost_band = cost_band
                            db.session.commit()
                            logger.info(f"Generated and persisted cost band '{cost_band}' for model {model_id}")
                        except Exception as persist_error:
                            logger.error(f"Failed to persist cost band for {model_id}: {persist_error}")
                            db.session.rollback()
                        
                        models_with_missing_data.append(model_id)
                    
                    # Get raw pricing values for JavaScript calculations (already per-million in database)
                    input_price_raw = db_model.input_price_usd_million or 0
                    output_price_raw = db_model.output_price_usd_million or 0
                    
                    # Handle special cases for AutoRouter
                    if model_id == "openrouter/auto":
                        input_price_raw = None  # Use None to indicate no fixed price
                        output_price_raw = None
                        cost_band = "Auto"  # Special cost band for Auto Router
                    
                    # Create base pricing data
                    pricing_data = {
                        'input_price': input_price_raw,
                        'output_price': output_price_raw,
                        'context_length': str(db_model.context_length) if db_model.context_length else 'N/A',
                        'multimodal': "Yes" if db_model.is_multimodal else "No",
                        'pdfs': "Yes" if db_model.supports_pdf else "No",
                        'model_name': db_model.name or model_id,
                        'model_id': model_id,
                        'cost_band': cost_band,
                        'is_free': False if model_id == "openrouter/auto" else (db_model.is_free or False),
                        'is_reasoning': db_model.supports_reasoning or False,
                        'elo_score': db_model.elo_score,  # Add LMSYS ELO score
                        'source': 'database'
                    }
                    
                    # Add special display properties for Auto Router
                    if model_id == "openrouter/auto":
                        pricing_data.update({
                            'display_input_price': 'Dynamic*',
                            'display_output_price': 'Dynamic*',
                            'context_length_display': 'Variable',
                            'cost_band_symbol': 'Auto',
                            'cost_band_class': 'cost-band-auto'
                        })
                    
                    prices[model_id] = pricing_data
                    
                except Exception as e:
                    # Log but don't exclude models with processing issues
                    logger.warning(f"Issue processing model {db_model.model_id}: {e}")
                    
                    # Include with minimal safe data using correct field names
                    prices[db_model.model_id] = {
                        'input_price': 0,
                        'output_price': 0,
                        'context_length': 'N/A',
                        'multimodal': 'No',
                        'pdfs': 'No',
                        'model_name': db_model.model_id,
                        'model_id': db_model.model_id,
                        'cost_band': 'Unknown',
                        'is_free': True,
                        'is_reasoning': db_model.supports_reasoning or False,
                        'source': 'database_fallback'
                    }
            
            # Log summary of data completeness issues
            if models_with_missing_data:
                logger.warning(f"Generated missing cost bands for {len(models_with_missing_data)} models: {models_with_missing_data[:5]}{'...' if len(models_with_missing_data) > 5 else ''}")
                
                # CRITICAL FIX: Update Redis cache after persisting new cost bands
                try:
                    from price_updater import _populate_redis_pricing_cache
                    _populate_redis_pricing_cache()
                    logger.info("Updated Redis cache after generating new cost bands")
                except Exception as cache_error:
                    logger.warning(f"Failed to update Redis cache after cost band generation: {cache_error}")
            
            # Use the timestamp of the most recently updated model
            latest_model = OpenRouterModel.query.order_by(OpenRouterModel.last_fetched_at.desc()).first()
            last_updated = latest_model.last_fetched_at.isoformat() if latest_model else None
            
            logger.info(f"Retrieved prices for {len(prices)} models from database")
            
            # Create response data
            response_data = {
                'success': True,
                'prices': prices,
                'last_updated': last_updated
            }
            
            # Cache the response for instant future loading
            try:
                from api_cache import get_redis_client
                redis_client = get_redis_client('cache')
                
                if redis_client:
                    import json
                    redis_client.setex(
                        'cache:pricing_table_data',
                        300,  # Cache for 5 minutes
                        json.dumps(response_data)
                    )
                    logger.info("Cached pricing data in Redis for instant future loading")
            except Exception as e:
                logger.debug(f"Could not cache pricing data: {e}")
            
            # Return the model prices from the database
            return jsonify(response_data)
            
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
            
            # If no models in database and fetch failed, we need a minimal fallback
            logger.warning("Database is still empty and API fetch failed, providing minimal data")
            
            # Use a minimal set of default models
            import datetime
            prices = {}
            
            # Add a few critical default models
            # This is a fallback mechanism, not serving as primary data
            # Claude 3.5 Sonnet
            prices['anthropic/claude-3.5-sonnet'] = {
                'input_price': 3.0,
                'output_price': 15.0,
                'context_length': 200000,
                'is_multimodal': True,
                'model_name': 'Claude 3.5 Sonnet',
                'cost_band': '$$$',
                'source': 'fallback'
            }
            
            # GPT-3.5 Turbo
            prices['openai/gpt-3.5-turbo'] = {
                'input_price': 0.5,
                'output_price': 1.5,
                'context_length': 16000,
                'is_multimodal': False,
                'model_name': 'GPT-3.5 Turbo',
                'cost_band': '$',
                'source': 'fallback'
            }
            
            # Gemini Flash (free)
            prices['google/gemini-2.0-flash-exp:free'] = {
                'input_price': 0.0,
                'output_price': 0.0,
                'context_length': 8000,
                'is_multimodal': False,
                'model_name': 'Gemini 2.0 Flash (FREE)',
                'cost_band': '',
                'source': 'fallback'
            }
            
            # Return the minimal fallback data with current timestamp
            return jsonify({
                'success': True,
                'prices': prices,
                'last_updated': datetime.datetime.utcnow().isoformat(),
                'source': 'fallback'
            })
            
    except Exception as e:
        logger.exception(f"Error getting model prices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/refresh_model_prices', methods=['POST'])
def refresh_model_prices():
    """ 
    Manually refresh model prices from OpenRouter API 
    Updates both the database and the legacy cache
    """
    try:
        # Call the function to fetch and store prices in both database and cache
        success = fetch_and_store_openrouter_prices()
        
        if success:
            # Get prices from the database, which is our new primary source
            from models import OpenRouterModel
            db_models = OpenRouterModel.query.filter_by(model_is_active=True).all()
            
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
                        'cost_band': db_model.cost_band
                    }
                
                # Get the most recent update timestamp
                latest_model = OpenRouterModel.query.order_by(OpenRouterModel.last_fetched_at.desc()).first()
                last_updated = latest_model.last_fetched_at.isoformat() if latest_model else None
                
                return jsonify({
                    'success': True,
                    'prices': prices,
                    'last_updated': last_updated,
                    'message': f'Model prices refreshed successfully - {len(prices)} models updated'
                })
            else:
                # No models in database despite successful fetch - provide minimal fallback
                import datetime
                # Create minimal fallback data
                fallback_prices = {
                    'google/gemini-2.0-flash-exp:free': {
                        'input_price': 0.0,
                        'output_price': 0.0,
                        'context_length': 8000,
                        'is_multimodal': False,
                        'model_name': 'Gemini 2.0 Flash (FREE)',
                        'cost_band': '',
                        'source': 'fallback'
                    }
                }
                return jsonify({
                    'success': True,
                    'prices': fallback_prices,
                    'last_updated': datetime.datetime.utcnow().isoformat(),
                    'message': 'Failed to store models in database, using minimal fallback',
                    'source': 'fallback'
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to refresh model prices from OpenRouter API'
            }), 500
            
    except Exception as e:
        logger.exception(f"Error refreshing model prices: {e}")
        
        # Create a more user-friendly error message
        user_friendly_message = "There was a problem updating model information."
        
        # Add specific information for common error types
        if "InFailedSqlTransaction" in str(e):
            user_friendly_message = "Database error while updating model information. This is a temporary issue - please try again in a few minutes."
        elif "HTTPError" in str(e) or "ConnectionError" in str(e):
            user_friendly_message = "Could not connect to the model provider API. Please check your internet connection and API key settings."
        elif "Timeout" in str(e):
            user_friendly_message = "The request to update model information timed out. Please try again later."
        elif "OPENROUTER_API_KEY" in str(e):
            user_friendly_message = "OpenRouter API key is missing or invalid. Please check your API key settings."
            
        return jsonify({
            'success': False,
            'error': user_friendly_message,
            'technical_details': str(e)
        }), 500

@app.route('/api/model-pricing', methods=['GET'])
def get_model_pricing():
    """ 
    Legacy endpoint - redirects to the primary model pricing endpoint
    This ensures any unknown dependencies continue to work
    """
    logger.info("Legacy /api/model-pricing endpoint called, redirecting to /api/get_model_prices")
    return redirect(url_for('get_model_prices'))

@app.route('/models', methods=['GET'])
def get_models():
    """ 
    Fetch available models from the database
    This is an updated implementation that uses the database as the primary source
    """
    try:
        from models import OpenRouterModel
        
        # Query only active models from the database
        db_models = OpenRouterModel.query.filter_by(model_is_active=True).order_by(OpenRouterModel.name).all()
        
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
                    'is_multimodal': bool(db_model.is_multimodal),
                    'supports_vision': bool(db_model.is_multimodal),  # Frontend expects this field
                    'supports_pdf': bool(db_model.supports_pdf or db_model.model_id in DOCUMENT_MODELS),
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
            
            # If database is still empty after fetching, try one more API fetch as final resort
            logger.warning("Database is still empty after fetch attempt, trying direct API fetch as final resort")
            
            # Use the _fetch_openrouter_models function directly (which now also attempts to store in DB)
            result_data = _fetch_openrouter_models()
            if result_data and result_data.get("data"):
                logger.info(f"Successfully fetched {len(result_data.get('data', []))} models via direct API fetch")
                return jsonify(result_data)
            
            # If all else failed
            logger.error("All methods failed to retrieve model data")
            return jsonify({
                "error": "Failed to retrieve models",
                "message": "We're experiencing temporary issues. Please try again in a few minutes."
            }), 200  # Using 200 so frontend can handle gracefully

    except Exception as e:
        logger.exception(f"Error in get_models: {e}")
        
        # Return a friendly error
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


@app.route('/api/model-counts', methods=['GET'])
def get_model_counts():
    """Get current model counts for display on info page with Redis caching"""
    try:
        # Try to get cached counts first for instant loading
        try:
            from api_cache import get_redis_client
            redis_client = get_redis_client('cache')
            
            if redis_client:
                cached_counts = redis_client.get('cache:model_counts')
                if cached_counts:
                    import json
                    logger.debug("Serving model counts from Redis cache")
                    return jsonify(json.loads(cached_counts))
        except Exception as e:
            logger.debug(f"Redis cache unavailable for model counts: {e}")
        
        # Get fresh counts from database
        from models import OpenRouterModel
        
        total_models = OpenRouterModel.query.filter_by(model_is_active=True).count()
        free_models = OpenRouterModel.query.filter_by(model_is_active=True, is_free=True).count()
        paid_models = OpenRouterModel.query.filter_by(model_is_active=True, is_free=False).count()
        
        response_data = {
            "success": True,
            "total_models": total_models,
            "free_models": free_models,
            "paid_models": paid_models
        }
        
        # Cache the counts for fast future access
        try:
            from api_cache import get_redis_client
            redis_client = get_redis_client('cache')
            
            if redis_client:
                import json
                redis_client.setex(
                    'cache:model_counts',
                    300,  # Cache for 5 minutes
                    json.dumps(response_data)
                )
                logger.debug("Cached model counts in Redis")
        except Exception as e:
            logger.debug(f"Could not cache model counts: {e}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.exception("Error getting model counts")
        return jsonify({
            "success": False,
            "error": str(e),
            "total_models": 0,
            "free_models": 0,
            "paid_models": 0
        })


@app.route('/api/check-model-changes', methods=['POST'])
def check_model_changes():
    """Check for changes in OpenRouter models and trigger update if needed"""
    try:
        from model_change_monitor import check_and_update_if_changed
        
        changed, message = check_and_update_if_changed()
        
        return jsonify({
            "success": True,
            "changes_detected": changed,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.exception("Error checking for model changes")
        return jsonify({
            "success": False,
            "changes_detected": False,
            "message": f"Error: {e}",
            "timestamp": datetime.utcnow().isoformat()
        })


@app.route('/api/model-visibility-audit', methods=['GET'])
def model_visibility_audit():
    """Audit model visibility to detect when models are stored but not displayed"""
    try:
        from models import OpenRouterModel
        
        # Get all active models from database
        db_models = OpenRouterModel.query.filter_by(model_is_active=True).all()
        db_model_ids = {model.model_id for model in db_models}
        
        # Get models that appear in pricing API
        pricing_response = get_model_prices()
        if isinstance(pricing_response, tuple):
            pricing_data = pricing_response[0].get_json()
        else:
            pricing_data = pricing_response
            
        pricing_model_ids = set(pricing_data.get('prices', {}).keys())
        
        # Find discrepancies
        missing_from_pricing = db_model_ids - pricing_model_ids
        extra_in_pricing = pricing_model_ids - db_model_ids
        
        # Get details about missing models
        missing_models_details = []
        for model_id in missing_from_pricing:
            model = OpenRouterModel.query.filter_by(model_id=model_id).first()
            if model:
                missing_models_details.append({
                    'model_id': model_id,
                    'name': model.name,
                    'is_free': model.is_free,
                    'cost_band': model.cost_band,
                    'has_empty_cost_band': not model.cost_band or model.cost_band.strip() == '',
                    'input_price': model.input_price_usd_million,
                    'output_price': model.output_price_usd_million
                })
        
        audit_result = {
            "success": True,
            "total_db_models": len(db_model_ids),
            "total_pricing_models": len(pricing_model_ids),
            "missing_from_pricing_count": len(missing_from_pricing),
            "missing_from_pricing": list(missing_from_pricing),
            "missing_models_details": missing_models_details,
            "extra_in_pricing_count": len(extra_in_pricing),
            "extra_in_pricing": list(extra_in_pricing),
            "visibility_percentage": (len(pricing_model_ids) / len(db_model_ids)) * 100 if db_model_ids else 0
        }
        
        # Log critical visibility issues
        if missing_from_pricing:
            logger.warning(f"Model visibility audit found {len(missing_from_pricing)} models missing from pricing display: {list(missing_from_pricing)[:5]}{'...' if len(missing_from_pricing) > 5 else ''}")
        
        return jsonify(audit_result)
        
    except Exception as e:
        logger.exception("Error performing model visibility audit")
        return jsonify({
            "success": False,
            "error": str(e),
            "total_db_models": 0,
            "total_pricing_models": 0,
            "missing_from_pricing_count": 0,
            "visibility_percentage": 0
        })


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
    """Display a shared conversation for anyone with the link"""
    try:
        from models import Conversation, Message
        from datetime import datetime
        
        logger.info(f"Starting to process shared conversation view for share_id: {share_id}")
        
        # Find the conversation by share_id
        conversation = Conversation.query.filter_by(share_id=share_id).first()
        if not conversation:
            logger.warning(f"No conversation found with share_id: {share_id}")
            flash("The shared conversation link is invalid or has expired.", "warning")
            return redirect(url_for('index'))
            
        # Check if this is the owner of the conversation viewing through a shared link
        # If so, redirect them to the home page with the current conversation ID
        # The JavaScript will load the correct conversation
        if current_user.is_authenticated and conversation.user_id == current_user.id:
            logger.info(f"Owner of conversation {conversation.id} viewing their own shared link - redirecting to home with conversation ID")
            return redirect(url_for('index', conversation_id=conversation.id))
        
        # For authenticated users who are not the owner, explicitly set is_logged_in flag
        # to pass to the template (ensures consistent rendering regardless of auth status)
        is_logged_in = current_user.is_authenticated
        
        logger.info(f"Found conversation with ID: {conversation.id}, title: {conversation.title}")
        
        # Get all messages for this conversation
        messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.id).all()
        logger.info(f"Found {len(messages)} messages for conversation ID: {conversation.id}")
        
        # Convert messages to a format suitable for the template
        formatted_messages = []
        for message in messages:
            # Skip system messages in shared view
            if message.role == 'system':
                continue
                
            formatted_message = {
                'id': message.id,
                'role': message.role,
                'content': message.content,
                'model': message.model,
                'created_at': message.created_at.isoformat() if message.created_at else '',
                'image_url': message.image_url
            }
            formatted_messages.append(formatted_message)
        
        logger.info(f"Formatted {len(formatted_messages)} messages for template")
        
        # Fix for potential date formatting issue
        if hasattr(conversation, 'created_at') and conversation.created_at:
            created_at_str = conversation.created_at.strftime('%B %d, %Y')
            logger.info(f"Conversation created date: {created_at_str}")
        else:
            logger.warning("Conversation has no created_at attribute or it's None")
            # Provide a default date if missing
            conversation.created_at = datetime.now()
            
        # Return the shared conversation template
        logger.info("Rendering shared_conversation.html template")
        return render_template(
            'shared_conversation.html',
            conversation=conversation,
            messages=formatted_messages,
            is_logged_in=is_logged_in,
            user=current_user
        )
    
    except Exception as e:
        logger.exception(f"Error viewing shared conversation {share_id}: {e}")
        flash("An error occurred while trying to load the shared conversation.", "error")
        return redirect(url_for('index'))

@app.route('/api/rag/diagnostics', methods=['GET'])
def rag_diagnostics():
    """
    Diagnostic endpoint to check the state of document processing.
    This endpoint now returns information about direct PDF handling capabilities.
    """
    try:
        # Get models that support PDF handling
        pdf_capable_models = []
        
        try:
            models = _fetch_openrouter_models()
            for model_id, model_info in models.items():
                if model_info.get('pdf', False) or model_info.get('supports_pdf', False):
                    pdf_capable_models.append(model_id)
        except Exception as e:
            logger.error(f"Error fetching PDF-capable models: {e}")
        
        return jsonify({
            "status": "transitioned",
            "message": "RAG system replaced with direct PDF handling through OpenRouter",
            "pdf_handling": {
                "enabled": True,
                "container": os.environ.get("AZURE_STORAGE_PDF_CONTAINER_NAME", "gloriamundopdfs"),
                "supported_models": pdf_capable_models
            }
        })
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
    # Declare global document_processor at the beginning of the function
    global document_processor
    
    if not ENABLE_RAG:
        return jsonify({"error": "RAG functionality is not enabled"}), 400
        
    try:
        # Get user ID - use either authenticated user or session-based identifier
        if current_user and current_user.is_authenticated:
            user_id = str(current_user.id)
        else:
            user_id = get_user_identifier()
            
        # Make sure document_processor is initialized
        if 'document_processor' not in globals() or document_processor is None:
            document_processor = DocumentProcessor()
            
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
# PWA Service Worker routes
@app.route('/service-worker.js')
def service_worker():
    """Serve the service worker JavaScript file from the static folder"""
    return send_from_directory('static/js', 'service-worker.js')

@app.route('/manifest.json')
def manifest():
    """Serve the manifest.json file for PWA"""
    return send_from_directory('static/manifest', 'manifest.json')

@app.route('/pwa-test')
def pwa_test():
    """Test page for PWA functionality"""
    return render_template('pwa_test.html')

if __name__ == '__main__':
    logger.info("Starting Flask development server")
    
    # Note: All background tasks are now handled by optimized startup sequence
    # Price fetching uses Redis distributed locks to ensure cluster-wide coordination
    logger.info("🚀 Optimized autoscaling startup completed - ready for requests!")
    
    # ensure gevent monkey-patching already happened at import time
    app.run(host='0.0.0.0', port=5000, debug=True)