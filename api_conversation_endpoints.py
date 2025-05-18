"""
API endpoints for conversation management (pin, rename).
These will be imported and registered in app.py.
"""

from flask import jsonify, request
from flask_login import current_user, login_required
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def register_conversation_endpoints(app, db):
    """Register the conversation management API endpoints with the Flask app."""
    
    @app.route('/api/pin_chat/<int:conversation_id>', methods=['PUT'])
    @login_required
    def pin_chat(conversation_id):
        """Toggle the pinned status of a conversation"""
        try:
            from models import Conversation
            
            # Find the conversation and verify ownership
            conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
            if not conversation:
                return jsonify({"success": False, "error": "Conversation not found or access denied."}), 404
                
            # Toggle the pinned status
            conversation.is_pinned = not conversation.is_pinned
            conversation.updated_at = datetime.utcnow()  # Update the timestamp
            
            # Save changes to database
            try:
                db.session.commit()
                return jsonify({
                    "success": True, 
                    "message": "Chat pin status updated.", 
                    "is_pinned": conversation.is_pinned
                })
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating pin status: {e}")
                return jsonify({"success": False, "error": "Failed to update pin status."}), 500
                
        except Exception as e:
            logger.error(f"Error in pin_chat endpoint: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/rename_chat/<int:conversation_id>', methods=['PUT'])
    @login_required
    def rename_chat(conversation_id):
        """Rename a conversation"""
        try:
            from models import Conversation
            
            # Get the new title from the request JSON data
            data = request.get_json()
            new_title = data.get('new_title')
            
            # Validate the new title
            if not new_title or len(new_title.strip()) == 0:
                return jsonify({"success": False, "error": "New title cannot be empty."}), 400
                
            # Find the conversation and verify ownership
            conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
            if not conversation:
                return jsonify({"success": False, "error": "Conversation not found or access denied."}), 404
                
            # Update the title
            conversation.title = new_title.strip()
            conversation.updated_at = datetime.utcnow()  # Update the timestamp
            
            # Save changes to database
            try:
                db.session.commit()
                return jsonify({
                    "success": True, 
                    "message": "Chat renamed successfully.", 
                    "new_title": conversation.title
                })
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error renaming chat: {e}")
                return jsonify({"success": False, "error": "Failed to rename chat."}), 500
                
        except Exception as e:
            logger.error(f"Error in rename_chat endpoint: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
            
    return app