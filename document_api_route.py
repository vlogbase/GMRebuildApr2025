"""
API route for getting active document information.
To be imported in app.py
"""
from flask import jsonify, session
from flask_login import login_required
import logging

logger = logging.getLogger(__name__)

def setup_document_api_routes(app):
    """
    Set up document API routes
    """
    @app.route('/api/conversation/<conversation_id>/active_document_info', methods=['GET'])
    @login_required
    def get_active_document_info(conversation_id):
        """ Get information about the active document for the current conversation """
        logger.debug(f"Getting active document info for conversation {conversation_id}")
        
        # Get active document context from session
        active_document_context = session.get('active_document_context', None)
        
        if not active_document_context:
            return jsonify({"active_document": None})
            
        # Handle both possible formats of active_document_context
        
        # Format 1: Direct document object with conversation_id field
        if isinstance(active_document_context, dict) and 'conversation_id' in active_document_context:
            if (active_document_context.get('conversation_id') == str(conversation_id) and
                active_document_context.get('doc_id') and
                active_document_context.get('filename')):
                
                return jsonify({
                    "active_document": {
                        "doc_id": active_document_context.get('doc_id'),
                        "filename": active_document_context.get('filename')
                    }
                })
        
        # Format 2: Dictionary with conversation_id as keys
        elif isinstance(active_document_context, dict):
            # Check if this conversation has an active document
            if str(conversation_id) in active_document_context:
                # This is just a flag in the current implementation, but we can
                # enhance it in the future to store actual document info
                # For now, we'll show a generic message
                return jsonify({
                    "active_document": {
                        "filename": "Document is active for this conversation"
                    }
                })
        
        # No active document for this conversation
        return jsonify({"active_document": None})