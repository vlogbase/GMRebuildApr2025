"""
Test script for the model fallback confirmation feature.

This script runs a simple Flask app that demonstrates the model fallback
confirmation dialog when a requested model is unavailable.
"""
import os
import logging
from flask import Flask, render_template, jsonify, request
from flask_login import current_user, login_required
from models import UserChatSettings

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    """Run the test app for model fallback confirmation"""
    try:
        from app import app, db
        
        @app.route('/test-fallback')
        def test_fallback_page():
            """Test page for model fallback confirmation"""
            # Get user settings if authenticated
            user_chat_settings = None
            if current_user and current_user.is_authenticated:
                user_chat_settings = UserChatSettings.query.filter_by(user_id=current_user.id).first()
            
            return render_template(
                'test_fallback.html',
                user=current_user if current_user.is_authenticated else None,
                user_chat_settings=user_chat_settings
            )
        
        @app.route('/api/test-fallback', methods=['POST'])
        def test_fallback_api():
            """Simulate a model fallback situation for testing"""
            try:
                data = request.json
                requested_model = data.get('model', 'anthropic/claude-3-haiku')
                requested_name = requested_model.split('/')[-1].replace('-', ' ').title()
                
                # Simulate fallback to Gemini Flash
                fallback_model_id = 'google/gemini-flash:free'
                fallback_model_name = 'Gemini Flash'
                
                # Return a fallback notification
                return jsonify({
                    'type': 'model_fallback',
                    'requested_model': requested_name,
                    'fallback_model': fallback_model_name,
                    'original_model_id': requested_model,
                    'fallback_model_id': fallback_model_id,
                    'reason': 'Model unavailable for testing purposes'
                })
            except Exception as e:
                logger.error(f"Error in test_fallback_api: {e}")
                return jsonify({
                    'error': str(e)
                }), 500
        
        # Print test instructions
        logger.info("=" * 80)
        logger.info("MODEL FALLBACK CONFIRMATION TEST")
        logger.info("=" * 80)
        logger.info("Test the model fallback confirmation feature by:")
        logger.info("1. Navigate to http://localhost:5000/test-fallback")
        logger.info("2. Click the 'Test Fallback Dialog' button to simulate a model fallback")
        logger.info("3. Toggle the auto-fallback setting to see how it changes the behavior")
        logger.info("=" * 80)
        
        return True
    except Exception as e:
        logger.error(f"Error setting up fallback test: {e}")
        return False

if __name__ == "__main__":
    run()