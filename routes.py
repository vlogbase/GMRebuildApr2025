"""
Routes module for GloriaMundo Chatbot

This module contains all route definitions imported by main.py
It references the app instance from main.py
"""
import os
import io
import json
import base64
import secrets
import datetime
import time
import logging
import uuid
import mimetypes
from pathlib import Path
from werkzeug.datastructures import FileStorage
from flask import render_template, request, Response, session, jsonify, abort
from flask import url_for, redirect, flash, stream_with_context, send_from_directory
from flask_login import current_user, login_required, login_user, logout_user
from PIL import Image
from urllib.parse import urlparse

# Import the app instance from main.py
from main import app, document_processor, ENABLE_RAG

# Import database models and other needed modules
from database import db
from models import User, Conversation, Message, UserPreference, UserChatSettings
from models import OpenRouterModel, SystemPrompt, CustomCSSJS
from user_settings import get_user_settings, save_user_settings, get_user_chat_settings

# Import global variables from app.py
from app import (
    VERSION, MODEL_INFO, MULTIMODAL_MODELS, DOCUMENT_MODELS, TOKEN_PRICES, DEFAULT_MODEL,
    OPENAI_API_KEY, OPENROUTER_API_KEY, MAX_HISTORY_LENGTH, SYSTEM_PROMPT,
    DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, logger
)

# Import utility functions from app.py
from app import (
    truncate_conversation_history, get_openrouter_chat_completion, 
    parse_openrouter_response, get_available_models, 
    get_conversation_by_id, get_user_conversations,
    get_user_identifier, create_new_conversation, 
    save_message, get_conversation_messages
)

# Initialize Azure storage for image uploads if available
USE_AZURE_STORAGE = False
try:
    from azure.storage.blob import BlobServiceClient, ContentSettings
    
    # Azure Blob Storage configuration
    azure_connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    azure_container_name = os.environ.get('AZURE_STORAGE_CONTAINER')
    
    if azure_connection_string and azure_container_name:
        blob_service_client = BlobServiceClient.from_connection_string(azure_connection_string)
        container_client = blob_service_client.get_container_client(azure_container_name)
        logger.info(f"Azure Blob Storage initialized successfully for container: {azure_container_name}")
        USE_AZURE_STORAGE = True
except Exception as e:
    logger.warning(f"Failed to initialize Azure Blob Storage: {e}")
    logger.info("Falling back to local storage for image uploads")
    USE_AZURE_STORAGE = False

# Import routing functions from app.py
@app.route('/')
def index():
    """Render the index page"""
    # Get user settings if authenticated
    user_settings = {}
    if current_user.is_authenticated:
        user_settings = get_user_settings(current_user.id)
    
    # Get available models
    models = get_available_models()
    
    return render_template('index.html', 
                          version=VERSION,
                          models=models,
                          default_model=DEFAULT_MODEL,
                          user_settings=user_settings)

@app.route('/chat')
def chat():
    """Render the chat interface"""
    # Get available models
    models = get_available_models()
    
    # Get user settings if authenticated
    user_settings = {}
    if current_user.is_authenticated:
        user_settings = get_user_settings(current_user.id)
        
    # Get chat settings
    chat_settings = get_user_chat_settings(
        current_user.id if current_user.is_authenticated else None
    )
    
    # Get conversation ID from query parameter or create a new one
    conversation_id = request.args.get('id')
    if conversation_id:
        # Get the conversation
        conversation = get_conversation_by_id(conversation_id)
        if not conversation:
            return redirect(url_for('chat'))
    else:
        # Create a new conversation
        conversation = create_new_conversation(
            user_id=current_user.id if current_user.is_authenticated else None,
            title="New Conversation"
        )
        conversation_id = conversation.id
    
    # Get the conversation messages
    messages = get_conversation_messages(conversation_id)
    
    # Get user conversations for the sidebar
    conversations = []
    if current_user.is_authenticated:
        conversations = get_user_conversations(current_user.id)
    
    return render_template('chat.html',
                          version=VERSION,
                          models=models,
                          default_model=DEFAULT_MODEL,
                          user_settings=user_settings,
                          chat_settings=chat_settings,
                          conversation=conversation,
                          messages=messages,
                          conversations=conversations,
                          enable_rag=ENABLE_RAG)

# Import additional routes from app.py as needed
# Add @app.route decorators to functions from app.py

# Import the model fallback confirmation route
@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for chat completions"""
    # Implementation copied from app.py's /api/chat route
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Get required parameters
        conversation_id = data.get('conversation_id')
        model = data.get('model', DEFAULT_MODEL)
        content = data.get('content', '').strip()
        
        # Validate input
        if not content:
            return jsonify({"error": "Message content cannot be empty"}), 400
            
        if not conversation_id:
            return jsonify({"error": "Conversation ID is required"}), 400
            
        # Get conversation
        conversation = get_conversation_by_id(conversation_id)
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404
            
        # Get user ID
        user_id = None
        if current_user.is_authenticated:
            user_id = current_user.id
            
        # Save user message
        save_message(
            conversation_id=conversation_id,
            role="user",
            content=content,
            user_id=user_id
        )
        
        # Get chat settings (temperature, etc.)
        chat_settings = get_user_chat_settings(user_id)
        
        # Get conversation history
        messages = get_conversation_messages(conversation_id)
        
        # Truncate history to stay within token limits
        history = truncate_conversation_history(messages, MAX_HISTORY_LENGTH)
        
        # Add system prompt at the beginning
        system_message = {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
        
        # Prepare messages for API call
        api_messages = [system_message] + history
        
        # Make the API call
        response_data = get_openrouter_chat_completion(
            messages=api_messages,
            model=model,
            temperature=chat_settings.get('temperature', DEFAULT_TEMPERATURE),
            max_tokens=chat_settings.get('max_tokens', DEFAULT_MAX_TOKENS)
        )
        
        # Parse the response
        ai_message = parse_openrouter_response(response_data)
        
        # Save AI response
        save_message(
            conversation_id=conversation_id,
            role="assistant",
            content=ai_message,
            user_id=user_id
        )
        
        return jsonify({
            "message": ai_message,
            "model": model
        })
        
    except Exception as e:
        logger.exception(f"Error in API chat: {e}")
        return jsonify({"error": str(e)}), 500

# Add more routes as needed
# ...

# Add a catch-all route for 404 errors
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.exception(f"Server error: {e}")
    return render_template('500.html'), 500