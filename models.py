from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    """User model for authentication and storing user information"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256))
    google_id = db.Column(db.String(128), unique=True, nullable=True, index=True)  # Unique ID from Google
    profile_picture = db.Column(db.String(512), nullable=True)  # Profile picture URL
    last_login_at = db.Column(db.DateTime, nullable=True)  # Track last login time
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    preferences = db.relationship('UserPreference', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set the password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Conversation(db.Model):
    """Conversation model to store chat sessions"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False, default="New Conversation")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    share_id = db.Column(db.String(64), unique=True, index=True)  # Shareable identifier for public access
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Conversation {self.id}: {self.title}>'


class Message(db.Model):
    """Message model to store individual messages in a conversation"""
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = db.Column(db.Text, nullable=False)
    model = db.Column(db.String(64), nullable=True)  # Which AI model was used
    rating = db.Column(db.Integer, nullable=True, default=None)  # User feedback: +1 for upvote, -1 for downvote
    model_id_used = db.Column(db.String(64), nullable=True)  # Exact model ID returned by the API
    prompt_tokens = db.Column(db.Integer, nullable=True)  # Number of prompt tokens used
    completion_tokens = db.Column(db.Integer, nullable=True)  # Number of completion tokens used
    image_url = db.Column(db.String(512), nullable=True)  # URL to an image for multimodal messages
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Message {self.id}: {self.role}>'


class UserPreference(db.Model):
    """User model preferences for preset model buttons"""
    id = db.Column(db.Integer, primary_key=True)
    user_identifier = db.Column(db.String(64), nullable=False, index=True)  # Temporary identifier or User ID
    preset_id = db.Column(db.Integer, nullable=False)  # 1-6 corresponding to preset number
    model_id = db.Column(db.String(64), nullable=False)  # OpenRouter model ID
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Link to user when logged in
    
    # Create a unique constraint for user_identifier and preset_id
    __table_args__ = (
        db.UniqueConstraint('user_identifier', 'preset_id', name='user_preset_unique'),
    )
    
    def __repr__(self):
        return f'<UserPreference {self.user_identifier}: Preset {self.preset_id} -> {self.model_id}>'