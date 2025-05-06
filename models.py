from datetime import datetime, timedelta
import uuid
import secrets
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import enum

class PaymentStatus(enum.Enum):
    """Payment status for transactions"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    
class AffiliateStatus(enum.Enum):
    """Status for affiliate accounts"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    
class CommissionStatus(enum.Enum):
    """Status for affiliate commissions"""
    HELD = "held"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"
    PAYOUT_FAILED = "payout_failed"

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
    is_admin = db.Column(db.Boolean, default=False)  # Admin privileges
    
    # Billing fields
    credits = db.Column(db.Integer, nullable=False, default=0)  # User's credit balance in credits (1 credit = $0.00001)
    
    # Relationships
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    preferences = db.relationship('UserPreference', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    usages = db.relationship('Usage', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set the password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def add_credits(self, amount):
        """Add credits to user's account"""
        self.credits += amount
        
    def deduct_credits(self, amount):
        """Deduct credits from user's account"""
        if self.credits >= amount:
            self.credits -= amount
            return True
        return False
    
    def get_balance_usd(self):
        """Get user's balance in USD format"""
        return self.credits / 100000.0  # Convert credits to dollars (1 credit = $0.00001)
    
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


class Transaction(db.Model):
    """Transaction model for tracking payments and credit purchases"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'), nullable=True)  # Link to package if applicable
    amount_usd = db.Column(db.Float, nullable=False)  # Amount in USD
    credits = db.Column(db.Integer, nullable=False)  # Amount in credits (1 credit = $0.00001)
    payment_method = db.Column(db.String(64), nullable=False, default="stripe")  # Payment method used
    payment_id = db.Column(db.String(128), nullable=True)  # Payment ID (PayPal ID or Stripe Session ID)
    stripe_payment_intent = db.Column(db.String(128), nullable=True)  # Stripe Payment Intent ID
    status = db.Column(db.String(20), nullable=False, default=PaymentStatus.PENDING.value)  # Payment status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transaction {self.id}: ${self.amount_usd} ({self.credits} credits)>'


class Usage(db.Model):
    """Usage model for tracking credit usage"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)  # Link to message if applicable
    credits_used = db.Column(db.Integer, nullable=False)  # Credits used
    model_id = db.Column(db.String(64), nullable=True)  # Model used
    usage_type = db.Column(db.String(20), nullable=False)  # Type of usage (e.g., "chat", "embedding")
    prompt_tokens = db.Column(db.Integer, nullable=True)  # Number of prompt tokens
    completion_tokens = db.Column(db.Integer, nullable=True)  # Number of completion tokens
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Usage {self.id}: {self.credits_used} credits for {self.usage_type}>'


class Package(db.Model):
    """Package model for predefined credit packages"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)  # Package name (e.g., "$5 Package")
    description = db.Column(db.String(256), nullable=True)  # Package description
    amount_usd = db.Column(db.Float, nullable=False)  # Amount in USD
    credits = db.Column(db.Integer, nullable=False)  # Credits provided
    is_active = db.Column(db.Boolean, default=True)
    stripe_price_id = db.Column(db.String(128), nullable=True)  # Stripe Price ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Package {self.id}: {self.name} (${self.amount_usd})>'


class Affiliate(db.Model):
    """Affiliate model for tracking affiliates and their referrals"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    paypal_email = db.Column(db.String(120), unique=True, nullable=False)
    paypal_email_verified_at = db.Column(db.DateTime, nullable=True)
    referral_code = db.Column(db.String(16), unique=True, nullable=False, index=True)
    referred_by_affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliate.id', ondelete='SET NULL'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=AffiliateStatus.ACTIVE.value)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer_referrals = db.relationship('CustomerReferral', backref='affiliate', lazy='dynamic')
    commissions = db.relationship('Commission', backref='affiliate', lazy='dynamic')
    # Self-referential relationship for two-tier tracking
    referred_affiliates = db.relationship('Affiliate', backref=db.backref('referred_by', remote_side=[id]), lazy='dynamic')
    
    def generate_referral_code(self):
        """Generate a unique referral code"""
        while True:
            code = secrets.token_urlsafe(8)[:8]  # Generate an 8-character unique code
            if not Affiliate.query.filter_by(referral_code=code).first():
                self.referral_code = code
                return code
                
    def __repr__(self):
        return f'<Affiliate {self.id}: {self.name} ({self.referral_code})>'


class CustomerReferral(db.Model):
    """CustomerReferral model for tracking customer referrals from affiliates"""
    id = db.Column(db.Integer, primary_key=True)
    customer_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliate.id'), nullable=False)
    signup_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with User
    customer = db.relationship('User', backref='referral', uselist=False)
    
    # Unique constraint to ensure a customer can only be referred once
    __table_args__ = (
        db.UniqueConstraint('customer_user_id', name='unique_customer_referral'),
    )
    
    def __repr__(self):
        return f'<CustomerReferral {self.id}: User {self.customer_user_id} referred by Affiliate {self.affiliate_id}>'


class Commission(db.Model):
    """Commission model for tracking affiliate commissions"""
    id = db.Column(db.Integer, primary_key=True)
    affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliate.id'), nullable=False)
    triggering_transaction_id = db.Column(db.String(128), nullable=False, index=True)
    stripe_payment_status = db.Column(db.String(20), nullable=False)
    purchase_amount_base = db.Column(db.Numeric(10, 4), nullable=False)  # Base amount in GBP for calculation
    commission_rate = db.Column(db.Numeric(6, 4), nullable=False)  # Decimal rate (e.g., 0.10 for 10%)
    commission_amount = db.Column(db.Numeric(10, 2), nullable=False)  # Commission amount in GBP
    commission_level = db.Column(db.Integer, nullable=False)  # 1 for L1, 2 for L2
    status = db.Column(db.String(20), nullable=False, default=CommissionStatus.HELD.value)
    commission_earned_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    commission_available_date = db.Column(db.DateTime, nullable=False)
    payout_batch_id = db.Column(db.String(128), nullable=True)  # PayPal Payout batch ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        """Initialize a new Commission with appropriate dates"""
        super(Commission, self).__init__(**kwargs)
        if 'commission_earned_date' not in kwargs:
            self.commission_earned_date = datetime.utcnow()
        if 'commission_available_date' not in kwargs:
            # Default to 30 days after earned date
            self.commission_available_date = self.commission_earned_date + timedelta(days=30)
    
    def __repr__(self):
        return f'<Commission {self.id}: {self.commission_amount} GBP for Affiliate {self.affiliate_id}>'