"""
Inspect OpenRouter Annotations

This script creates a proxy handler for OpenRouter requests and responses
to inspect annotations being sent and received.
"""

import os
import json
import logging
import argparse
import requests
from flask import Flask, request, Response, jsonify
from werkzeug.serving import run_simple
from sqlalchemy import create_engine, text
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("openrouter_annotations.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create a Flask app for the proxy
app = Flask(__name__)

# OpenRouter API URL
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def get_annotations_from_database(message_id):
    """
    Get annotations from the database for a specific message.
    
    Args:
        message_id: The ID of the message
        
    Returns:
        dict: The annotations, or None if not found
    """
    try:
        # Get database URL from environment
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            return None
            
        # Create engine
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            query = text("""
                SELECT annotations FROM message 
                WHERE id = :message_id
            """)
                
            result = conn.execute(query, {"message_id": message_id})
            row = result.fetchone()
            
            if row:
                annotations = row[0]
                logger.info(f"Found annotations for message {message_id}: {annotations}")
                return annotations
            else:
                logger.warning(f"No annotations found for message {message_id}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting annotations from database: {e}")
        return None

@app.route('/proxy/openrouter', methods=['POST'])
def proxy_openrouter():
    """
    Proxy for OpenRouter API requests.
    Logs and analyzes annotations in both requests and responses.
    """
    try:
        # Get the original request data
        data = request.get_json()
        
        # Log the request
        formatted_json = json.dumps(data, indent=2)
        logger.info(f"=== OpenRouter Request ===\n{formatted_json}")
        
        # Check for annotations in the request
        if 'annotations' in data:
            logger.info(f"REQUEST HAS ANNOTATIONS: {json.dumps(data['annotations'], indent=2)}")
        else:
            logger.info("REQUEST DOES NOT HAVE ANNOTATIONS")
        
        # Get OpenRouter API key from environment
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            return jsonify({"error": "OPENROUTER_API_KEY environment variable not set"}), 500
        
        # Prepare headers
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://gloriamundo.com'
        }
        
        # Forward the request to OpenRouter
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=data,
            stream=True
        )
        
        # Stream the response through our proxy
        def generate():
            annotations_found = False
            annotation_data = None
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunk_text = chunk.decode('utf-8')
                    
                    # Check for annotations in the response
                    if not annotations_found and '"annotations"' in chunk_text:
                        logger.info(f"FOUND ANNOTATIONS IN RESPONSE: {chunk_text}")
                        annotations_found = True
                        
                        # Try to extract the annotations
                        try:
                            chunk_json = json.loads(chunk_text.replace('data: ', ''))
                            if 'annotations' in chunk_json:
                                annotation_data = chunk_json['annotations']
                        except Exception as e:
                            logger.error(f"Error extracting annotations from chunk: {e}")
                    
                    yield chunk
            
            # Log whether annotations were found
            if not annotations_found:
                logger.info("NO ANNOTATIONS FOUND IN RESPONSE")
        
        # Return the response with the same status code and headers
        return Response(
            generate(),
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    
    except Exception as e:
        logger.error(f"Error in proxy: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/inspect/message/<int:message_id>', methods=['GET'])
def inspect_message(message_id):
    """
    Inspect annotations for a specific message.
    """
    annotations = get_annotations_from_database(message_id)
    if annotations:
        return jsonify({
            "message_id": message_id,
            "has_annotations": True,
            "annotations": annotations
        })
    else:
        return jsonify({
            "message_id": message_id,
            "has_annotations": False
        })

@app.route('/inspect/conversation/<int:conversation_id>', methods=['GET'])
def inspect_conversation(conversation_id):
    """
    Inspect all messages and annotations in a conversation.
    """
    try:
        # Get database URL from environment
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return jsonify({"error": "DATABASE_URL environment variable not set"}), 500
            
        # Create engine
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            query = text("""
                SELECT id, role, content, annotations, created_at
                FROM message 
                WHERE conversation_id = :conversation_id
                ORDER BY created_at ASC
            """)
                
            result = conn.execute(query, {"conversation_id": conversation_id})
            messages = []
            
            for row in result:
                message_id, role, content, annotations, created_at = row
                messages.append({
                    "id": message_id,
                    "role": role,
                    "content_preview": content[:100] + "..." if len(content) > 100 else content,
                    "has_annotations": annotations is not None,
                    "annotations": annotations,
                    "created_at": created_at.isoformat() if created_at else None
                })
            
            return jsonify({
                "conversation_id": conversation_id,
                "message_count": len(messages),
                "messages": messages
            })
                
    except Exception as e:
        logger.error(f"Error inspecting conversation: {e}")
        return jsonify({"error": str(e)}), 500

def main():
    parser = argparse.ArgumentParser(description='Inspect OpenRouter Annotations')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the proxy on')
    parser.add_argument('--message-id', type=int, help='Inspect a specific message ID')
    parser.add_argument('--conversation-id', type=int, help='Inspect a specific conversation ID')
    
    args = parser.parse_args()
    
    if args.message_id:
        # Just inspect a specific message
        annotations = get_annotations_from_database(args.message_id)
        if annotations:
            print(f"Annotations for message {args.message_id}:")
            print(json.dumps(annotations, indent=2))
        else:
            print(f"No annotations found for message {args.message_id}")
        return
    
    # Run the proxy server
    logger.info(f"Starting OpenRouter Annotations Inspector on port {args.port}")
    logger.info(f"Proxy endpoint: http://localhost:{args.port}/proxy/openrouter")
    logger.info(f"To inspect messages: http://localhost:{args.port}/inspect/message/<message_id>")
    logger.info(f"To inspect conversations: http://localhost:{args.port}/inspect/conversation/<conversation_id>")
    
    run_simple('localhost', args.port, app, use_reloader=True)

if __name__ == "__main__":
    main()