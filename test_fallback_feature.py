"""
Test script for the model fallback confirmation feature.

This script tests both the backend and frontend components of the model fallback
confirmation feature, including the user preference setting and the confirmation dialog.
"""
import os
import logging
from flask import render_template, request, jsonify
from app import app, db
from models import UserChatSettings, User
from flask_login import login_user, current_user

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test user credentials (use environment variables in a real application)
TEST_USER_EMAIL = "test@example.com"
TEST_USER_ID = 1

def create_test_user_if_not_exists():
    """Create a test user if it doesn't exist"""
    with app.app_context():
        user = User.query.filter_by(email=TEST_USER_EMAIL).first()
        if not user:
            logger.info(f"Creating test user: {TEST_USER_EMAIL}")
            user = User(
                id=TEST_USER_ID,
                email=TEST_USER_EMAIL,
                name="Test User",
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"Test user created with ID: {user.id}")
        return user

def create_test_routes():
    """Create test routes for the fallback feature"""
    
    @app.route('/test/fallback', methods=['GET'])
    def test_fallback_page():
        """Test page to trigger and visualize the model fallback confirmation dialog"""
        # Get user settings to pass to the template
        user_chat_settings = None
        if current_user.is_authenticated:
            user_chat_settings = UserChatSettings.query.filter_by(user_id=current_user.id).first()
        
        return render_template(
            'test_fallback.html',
            user=current_user,
            user_chat_settings=user_chat_settings
        )
    
    @app.route('/test/api/simulate_fallback', methods=['POST'])
    def simulate_fallback():
        """
        API endpoint to simulate a model fallback situation.
        This endpoint returns a model_fallback event to trigger the frontend dialog.
        """
        try:
            data = request.json
            requested_model = data.get('model', 'anthropic/claude-3-haiku')
            
            # Simulate fallback to a different model
            fallback_model_id = 'google/gemini-2.0-flash-exp:free'
            fallback_model_name = 'Gemini Flash'
            
            # Return a fallback notification
            return jsonify({
                'type': 'model_fallback',
                'requested_model': requested_model,
                'fallback_model': fallback_model_name,
                'original_model_id': requested_model,
                'fallback_model_id': fallback_model_id,
                'reason': 'Model unavailable for testing'
            })
        except Exception as e:
            logger.error(f"Error in simulate_fallback: {e}")
            return jsonify({
                'error': str(e)
            }), 500

def create_test_chat_settings():
    """Create or update test chat settings"""
    with app.app_context():
        user = User.query.filter_by(email=TEST_USER_EMAIL).first()
        if not user:
            logger.error("Test user not found")
            return
        
        # Get or create chat settings
        chat_settings = UserChatSettings.query.filter_by(user_id=user.id).first()
        if not chat_settings:
            logger.info(f"Creating chat settings for user: {user.id}")
            chat_settings = UserChatSettings(
                user_id=user.id,
                session_memory_enabled=True,
                auto_fallback_enabled=False  # Start with auto-fallback disabled
            )
            db.session.add(chat_settings)
        else:
            logger.info(f"Updating existing chat settings for user: {user.id}")
            chat_settings.auto_fallback_enabled = False
        
        db.session.commit()
        logger.info(f"Chat settings: auto_fallback_enabled={chat_settings.auto_fallback_enabled}")

def run_tests():
    """Run all tests for the fallback feature"""
    try:
        # Create test user if needed
        user = create_test_user_if_not_exists()
        
        # Create or update test chat settings
        create_test_chat_settings()
        
        # Create test routes
        create_test_routes()
        
        # Log test setup completion
        logger.info("Model fallback confirmation test setup complete")
        logger.info("Access the test page at: http://localhost:5000/test/fallback")
        
        # Return success
        return True
    except Exception as e:
        logger.error(f"Error setting up fallback tests: {e}")
        return False

if __name__ == "__main__":
    run_tests()