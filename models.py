"""
Models for GloriaMundo application
"""
from app import db
from flask_login import UserMixin
from datetime import datetime, timedelta
from sqlalchemy.sql import func
import uuid
import json
import os

class User(UserMixin, db.Model):
    """User model for authentication and profile management"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    google_id = db.Column(db.String(120), unique=True, nullable=True)
    name = db.Column(db.String(120), nullable=True)
    profile_picture = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade="all, delete-orphan")
    preferences = db.relationship('UserPreference', backref='user', lazy=True, cascade="all, delete-orphan")
    chat_settings = db.relationship('UserChatSettings', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def get_id(self):
        return str(self.id)

class UserPreference(db.Model):
    """User preferences for models and other settings"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    model = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserChatSettings(db.Model):
    """User settings for the chat interface"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_memory_enabled = db.Column(db.Boolean, default=True)
    auto_fallback_enabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Conversation(db.Model):
    """Conversation model for storing chat sessions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    share_id = db.Column(db.String(36), nullable=True, unique=True)
    
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade="all, delete-orphan")

class Message(db.Model):
    """Message model for storing individual messages in a conversation"""
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=True)
    model = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rating = db.Column(db.Integer, nullable=True)
    metadata = db.Column(db.Text, nullable=True)  # JSON string with additional info