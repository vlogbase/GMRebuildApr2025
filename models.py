from datetime import datetime, timedelta
import uuid
import secrets
import string
import logging
from database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import enum
from sqlalchemy import Text

class PaymentStatus(enum.Enum):
    """Payment status for transactions"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class CommissionStatus(enum.Enum):
    """Commission status for affiliate payouts"""
    HELD = "held"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"
    PAYOUT_FAILED = "payout_failed"
    PAYOUT_INITIATED = "payout_initiated"

class AffiliateStatus(enum.Enum):
    """Status for affiliate accounts"""
    PENDING_TERMS = "pending_terms"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

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
    user_is_active = db.Column(db.Boolean, default=True)  # Whether this user account is active
    
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
    pdf_url = db.Column(db.Text, nullable=True)  # URL or data URL for PDF document (can be large)
    pdf_filename = db.Column(db.String(255), nullable=True)  # Name of the PDF file
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
    """Affiliate model for the affiliate program"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    paypal_email = db.Column(db.String(120), nullable=True, unique=True)
    paypal_email_verified_at = db.Column(db.DateTime, nullable=True)
    referral_code = db.Column(db.String(16), nullable=False, unique=True, index=True)
    referred_by_affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliate.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=AffiliateStatus.PENDING_TERMS.value)
    terms_agreed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    referrals = db.relationship('Affiliate', backref=db.backref('referred_by', remote_side=[id]), lazy='dynamic')
    customer_referrals = db.relationship('CustomerReferral', backref='affiliate', lazy='dynamic', cascade='all, delete-orphan')
    commissions = db.relationship('Commission', backref='affiliate', lazy='dynamic', cascade='all, delete-orphan')
    
    @staticmethod
    def create_affiliate(name, email, paypal_email=None, referred_by_code=None, status=AffiliateStatus.PENDING_TERMS.value):
        """Create a new affiliate with a unique referral code"""
        # Generate a unique referral code
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(8))
            # Check if code already exists
            existing = Affiliate.query.filter_by(referral_code=code).first()
            if not existing:
                break
                
        affiliate = Affiliate(
            name=name,
            email=email,
            paypal_email=paypal_email,
            referral_code=code,
            status=status
        )
        
        # If referred by another affiliate, set the relationship
        if referred_by_code:
            referring_affiliate = Affiliate.query.filter_by(referral_code=referred_by_code).first()
            if referring_affiliate:
                affiliate.referred_by_affiliate_id = referring_affiliate.id
        
        return affiliate
        
    @staticmethod
    def auto_create_for_user(user):
        """Automatically create an affiliate record for a new user"""
        try:
            # Check if affiliate already exists
            existing_affiliate = Affiliate.query.filter_by(email=user.email).first()
            if existing_affiliate:
                return existing_affiliate
                
            # Generate a new affiliate with pending terms status
            affiliate = Affiliate.create_affiliate(
                name=user.username,
                email=user.email,
                status=AffiliateStatus.PENDING_TERMS.value
            )
            
            # Save to database
            db.session.add(affiliate)
            db.session.commit()
            
            return affiliate
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error auto-creating affiliate for user {user.id}: {e}")
            db.session.rollback()
            return None
            
    def agree_to_terms(self, paypal_email=None):
        """Mark affiliate as having agreed to terms and set paypal email if provided"""
        self.status = AffiliateStatus.ACTIVE.value
        self.terms_agreed_at = datetime.utcnow()
        
        if paypal_email:
            self.paypal_email = paypal_email
            
        return self
    
    def __repr__(self):
        return f'<Affiliate {self.id}: {self.name} ({self.email})>'


class CustomerReferral(db.Model):
    """Customer referral model to track which affiliate referred a customer"""
    id = db.Column(db.Integer, primary_key=True)
    customer_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliate.id'), nullable=False)
    signup_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    first_commissioned_purchase_at = db.Column(db.DateTime, nullable=True)
    
    # Create a unique constraint for customer_user_id
    __table_args__ = (
        db.UniqueConstraint('customer_user_id', name='customer_affiliate_unique'),
    )
    
    # Relationships
    customer = db.relationship('User', backref=db.backref('referral_info', uselist=False))
    
    def is_within_commission_window(self, transaction_date=None):
        """
        Check if a transaction date is within the one-year commission window.
        
        Args:
            transaction_date (datetime, optional): The date of the transaction to check.
                If None, uses the current UTC time.
                
        Returns:
            bool: True if the transaction date is within one year of the first commissioned purchase,
                  or if there's no first purchase yet. False otherwise.
        """
        if not self.first_commissioned_purchase_at:
            # No first purchase yet, so any transaction is eligible
            return True
            
        if transaction_date is None:
            transaction_date = datetime.utcnow()
            
        # Calculate the end of the eligibility window (one year after first purchase)
        eligibility_end_date = self.first_commissioned_purchase_at + timedelta(days=365)
        
        # Check if transaction_date is before or equal to eligibility_end_date
        return transaction_date <= eligibility_end_date
    
    def __repr__(self):
        return f'<CustomerReferral {self.id}: User {self.customer_user_id} referred by Affiliate {self.affiliate_id}>'


class OpenRouterModel(db.Model):
    """Model to store OpenRouter model information centrally in the database"""
    model_id = db.Column(db.String(128), primary_key=True)  # OpenRouter model ID (e.g., "google/gemini-pro")
    name = db.Column(db.String(128), nullable=True)  # Human-readable name
    description = db.Column(Text, nullable=True)  # Model description
    context_length = db.Column(db.Integer, nullable=True)  # Maximum context length
    input_price_usd_million = db.Column(db.Float, nullable=True)  # Markup price per million input tokens
    output_price_usd_million = db.Column(db.Float, nullable=True)  # Markup price per million output tokens
    is_multimodal = db.Column(db.Boolean, default=False)  # Whether model supports images
    is_free = db.Column(db.Boolean, default=False)  # Free models
    supports_reasoning = db.Column(db.Boolean, default=False)  # Models with strong reasoning capabilities
    supports_pdf = db.Column(db.Boolean, default=False)  # Whether model supports PDF files
    cost_band = db.Column(db.String(8), nullable=True)  # '$', '$$', '$$$', '$$$$' band
    model_is_active = db.Column(db.Boolean, default=True)  # Whether model is still available from OpenRouter
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # When this model record was created
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Last model data update
    last_fetched_at = db.Column(db.DateTime, default=datetime.utcnow)  # Last API fetch time
    
    def __repr__(self):
        return f'<OpenRouterModel {self.model_id}: {self.name}>'
        
    @classmethod
    def get_all_models(cls):
        """Return all active models ordered by name"""
        return cls.query.filter_by(model_is_active=True).order_by(cls.name).all()
        
    @classmethod
    def get_multimodal_models(cls):
        """Return only active multimodal models"""
        return cls.query.filter_by(is_multimodal=True, model_is_active=True).order_by(cls.name).all()
        
    @classmethod
    def get_pdf_models(cls):
        """Return only active models that support PDF files"""
        return cls.query.filter_by(supports_pdf=True, model_is_active=True).order_by(cls.name).all()
        
    @classmethod
    def is_model_multimodal(cls, model_id):
        """Check if a specific model supports multimodal inputs"""
        model = cls.query.get(model_id)
        if model:
            return model.is_multimodal
        # Default to False if model not found
        return False
        
    @classmethod
    def is_model_pdf_capable(cls, model_id):
        """Check if a specific model supports PDF files directly"""
        model = cls.query.get(model_id)
        if model:
            return model.supports_pdf
        # Default to False if model not found
        return False
        
    @classmethod
    def get_models_by_cost_band(cls, max_cost_band='$$$$'):
        """
        Return models filtered by maximum cost band
        Cost bands are ordered as: '' (free), '$', '$$', '$$$', '$$$$'
        """
        # Map cost bands to numeric values for comparison
        band_values = {
            '': 0,
            '$': 1,
            '$$': 2,
            '$$$': 3,
            '$$$$': 4
        }
        
        max_band_value = band_values.get(max_cost_band, 4)  # Default to highest if invalid
        
        # Get only active models
        all_models = cls.query.filter_by(model_is_active=True).all()
        
        # Filter based on band value
        filtered_models = []
        for model in all_models:
            model_band = model.cost_band or ''
            model_band_value = band_values.get(model_band, 0)
            
            if model_band_value <= max_band_value:
                filtered_models.append(model)
                
        return filtered_models


class Commission(db.Model):
    """Commission model for tracking affiliate commissions"""
    id = db.Column(db.Integer, primary_key=True)
    affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliate.id'), nullable=False)
    triggering_transaction_id = db.Column(db.String(128), nullable=False, index=True)  # Stripe payment intent ID
    stripe_payment_status = db.Column(db.String(32), nullable=False)
    purchase_amount_base = db.Column(db.Float(precision=4), nullable=False)  # Base amount in GBP
    commission_rate = db.Column(db.Float(precision=4), nullable=False)  # Commission rate (e.g., 0.10)
    commission_amount = db.Column(db.Float(precision=2), nullable=False)  # Commission amount in GBP
    commission_level = db.Column(db.Integer, nullable=False)  # 1 for L1, 2 for L2
    status = db.Column(db.String(32), nullable=False, default=CommissionStatus.HELD.value)
    commission_earned_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    commission_available_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(days=30))
    payout_batch_id = db.Column(db.String(128), nullable=True)  # PayPal payout batch ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Commission {self.id}: £{self.commission_amount} to Affiliate {self.affiliate_id} (Level {self.commission_level})>'