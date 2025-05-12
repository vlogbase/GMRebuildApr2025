"""
Test script to verify the PDF conversation creation fix
This script focuses on just the conversation creation part
"""

import os
import logging
import sys
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin, LoginManager, login_required, current_user, AnonymousUserMixin
import uuid
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Basic Flask and database setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'test_secret_key'

# Set up database
db = SQLAlchemy(app)

# Define minimal models for the test
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    
    @staticmethod
    def get_anonymous_user():
        return User.query.filter_by(username='anonymous').first()

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False, default="New Conversation")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    share_id = db.Column(db.String(64), unique=True, index=True)  # Shareable identifier for public access
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    @staticmethod
    def get_or_create_conversation(user_id, conversation_id=None):
        """Get existing conversation or create a new one"""
        if conversation_id:
            # Try to find existing conversation
            conversation = Conversation.query.filter_by(
                id=conversation_id, 
                user_id=user_id
            ).first()
            if conversation:
                return conversation
                
        # Create new conversation
        from secrets import token_hex
        share_id = token_hex(8)  # Generate a simple share_id for testing
        
        conversation = Conversation(
            title="PDF Conversation",
            user_id=user_id,
            share_id=share_id
        )
        db.session.add(conversation)
        db.session.commit()
        logger.info(f"Created new conversation with ID {conversation.id} for user {user_id}")
        return conversation

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=True, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_url = db.Column(db.Text, nullable=True)
    pdf_filename = db.Column(db.String(255), nullable=True)

# Set up login manager
login_manager = LoginManager()
login_manager.init_app(app)

class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.id = -1
        
    @property
    def is_authenticated(self):
        return False

login_manager.anonymous_user = Anonymous

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Mock route for testing conversation creation
@app.route('/upload_pdf_test', methods=['POST'])
def upload_pdf_test():
    """
    Test route that simulates the PDF upload function but focuses just on conversation creation
    """
    try:
        # Get conversation_id from query parameters if provided
        conversation_id = request.args.get('conversation_id')
        
        # Get or create user (using anonymous user for testing)
        user = User.get_anonymous_user()
        if not user:
            user = User(email='anonymous@example.com', username='anonymous')
            db.session.add(user)
            db.session.commit()
            logger.info(f"Created anonymous user with ID {user.id}")
        
        # Get or create conversation
        conversation = Conversation.get_or_create_conversation(user.id, conversation_id)
        
        # Create a placeholder message with PDF data
        pdf_message = Message(
            conversation_id=conversation.id,
            role='user',
            content='', # Empty content since the PDF is the content
            pdf_url='data:application/pdf;base64,dGVzdHBkZg==',  # Dummy base64 for "testpdf"
            pdf_filename='test.pdf'
        )
        db.session.add(pdf_message)
        db.session.commit()
        logger.info(f"Saved PDF message {pdf_message.id} for conversation {conversation.id}")
        
        return jsonify({
            "success": True,
            "message": "PDF upload simulation successful",
            "conversation_id": conversation.uuid,
            "user_id": user.id
        })
    
    except Exception as e:
        logger.exception(f"Error in test route: {e}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

def init_db():
    """Create database tables and initialize test data"""
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")

def run_test():
    """Run test to verify conversation creation"""
    # Test 1: Upload without conversation_id (should create new conversation)
    with app.test_client() as client:
        response = client.post('/upload_pdf_test')
        data = response.get_json()
        
        logger.info(f"Test 1 response: {data}")
        if data.get('success') and data.get('conversation_id'):
            logger.info("✅ Test 1 passed: Successfully created conversation")
            
            # Test 2: Upload with the same conversation_id (should use existing conversation)
            conv_id = data.get('conversation_id')
            response2 = client.post(f'/upload_pdf_test?conversation_id={conv_id}')
            data2 = response2.get_json()
            
            logger.info(f"Test 2 response: {data2}")
            if data2.get('success') and data2.get('conversation_id') == conv_id:
                logger.info("✅ Test 2 passed: Successfully used existing conversation")
                return True
        
        logger.error("❌ Test failed")
        return False

if __name__ == "__main__":
    init_db()
    success = run_test()
    if success:
        print("\n✅ All tests passed! The conversation creation fix is working correctly.")
    else:
        print("\n❌ Tests failed. The conversation creation fix needs further work.")
        exit(1)