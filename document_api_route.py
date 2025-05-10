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
        
        # Check if there's an active document for this conversation
        if (active_document_context and 
            isinstance(active_document_context, dict) and
            active_document_context.get('conversation_id') == str(conversation_id) and
            active_document_context.get('doc_id') and
            active_document_context.get('filename')):
            
            return jsonify({
                "active_document": {
                    "doc_id": active_document_context.get('doc_id'),
                    "filename": active_document_context.get('filename')
                }
            })
        
        # No active document for this conversation
        return jsonify({"active_document": None})