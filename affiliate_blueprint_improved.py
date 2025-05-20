"""
Affiliate Blueprint Module (Improved)

This module provides a Flask blueprint for the affiliate system.
This implementation resolves circular import issues and prevents the blueprint 
from being registered multiple times.
"""

import os
import time
import json
import uuid
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional, Any, Union

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app, flash, session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
affiliate_bp = Blueprint('affiliate', __name__, url_prefix='/affiliate', template_folder='templates')

# Define all routes before the blueprint is registered
@affiliate_bp.route('/dashboard')
def dashboard():
    """Affiliate dashboard view"""
    # Import database models inside function to avoid circular imports
    from database import User, Affiliate, Commission, Transaction, CustomerReferral, db
    
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to access your affiliate dashboard', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get user's affiliate info
    affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    
    if not affiliate:
        # User is not an affiliate yet, redirect to registration
        return redirect(url_for('affiliate.register'))
    
    # Get affiliate commissions
    commissions = Commission.query.filter_by(affiliate_id=affiliate.id).order_by(Commission.created_at.desc()).all()
    
    # Get referrals
    referrals = CustomerReferral.query.filter_by(affiliate_id=affiliate.id).order_by(CustomerReferral.created_at.desc()).all()
    
    # Calculate stats
    total_earned = sum(c.commission_amount for c in commissions if c.status in ['approved', 'paid'])
    total_pending = sum(c.commission_amount for c in commissions if c.status in ['pending', 'ready'])
    total_referrals = len(referrals)
    total_conversions = sum(1 for r in referrals if r.converted)
    conversion_rate = (total_conversions / total_referrals * 100) if total_referrals > 0 else 0
    
    # Calculate earnings by month (for chart)
    monthly_data = {}
    for commission in commissions:
        if commission.status in ['approved', 'paid']:
            month_key = commission.created_at.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = 0
            monthly_data[month_key] += commission.commission_amount
    
    # Ensure at least 6 months of data for the chart
    months = []
    values = []
    today = datetime.now()
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_key = month_date.strftime('%Y-%m')
        month_label = month_date.strftime('%b %Y')
        months.append(month_label)
        values.append(monthly_data.get(month_key, 0))
    
    # Get recent activity
    recent_activity = []
    
    # Add commissions to activity
    for commission in commissions[:10]:
        activity = {
            'type': 'commission',
            'date': commission.created_at,
            'amount': f'${commission.commission_amount:.2f}',
            'status': commission.status,
            'description': f'Commission from purchase (Level {commission.commission_level})'
        }
        recent_activity.append(activity)
    
    # Add referrals to activity
    for referral in referrals[:10]:
        activity = {
            'type': 'referral',
            'date': referral.created_at,
            'amount': None,
            'status': 'converted' if referral.converted else 'pending',
            'description': f'New referral: {referral.referral_source}'
        }
        recent_activity.append(activity)
    
    # Sort by date
    recent_activity.sort(key=lambda x: x['date'], reverse=True)
    recent_activity = recent_activity[:10]
    
    return render_template(
        'affiliate/dashboard.html',
        affiliate=affiliate,
        commissions=commissions,
        referrals=referrals,
        total_earned=total_earned,
        total_pending=total_pending,
        total_referrals=total_referrals,
        total_conversions=total_conversions,
        conversion_rate=conversion_rate,
        recent_activity=recent_activity,
        chart_months=json.dumps(months),
        chart_values=json.dumps(values)
    )

@affiliate_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register as an affiliate"""
    # Import database models inside function to avoid circular imports
    from database import User, Affiliate, db
    
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to register as an affiliate', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # Check if user is already an affiliate
    existing_affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    if existing_affiliate:
        flash('You are already registered as an affiliate', 'info')
        return redirect(url_for('affiliate.dashboard'))
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        paypal_email = request.form.get('paypal_email', '').strip()
        website = request.form.get('website', '').strip()
        terms_agreed = request.form.get('terms_agreed') == 'on'
        
        # Validate
        errors = []
        if not name:
            errors.append('Name is required')
        if not email:
            errors.append('Email is required')
        if not paypal_email:
            errors.append('PayPal email is required for receiving payments')
        if not terms_agreed:
            errors.append('You must agree to the affiliate terms')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('affiliate/register.html', user=user)
        
        # Generate a unique referral code
        referral_code = str(uuid.uuid4())[:8]
        
        # Create new affiliate
        affiliate = Affiliate(
            user_id=user_id,
            name=name,
            email=email,
            paypal_email=paypal_email,
            website=website,
            referral_code=referral_code,
            status='active',
            terms_agreed=True,
            terms_agreed_at=datetime.now()
        )
        
        try:
            db.session.add(affiliate)
            db.session.commit()
            flash('You have successfully registered as an affiliate!', 'success')
            return redirect(url_for('affiliate.dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering affiliate: {str(e)}")
            flash('An error occurred while registering. Please try again.', 'error')
    
    return render_template('affiliate/register.html', user=user)

@affiliate_bp.route('/terms')
def terms():
    """Display affiliate terms and conditions"""
    # Import database models inside function to avoid circular imports
    from database import User, Affiliate, db
    
    # Check if user is logged in
    user_is_logged_in = 'user_id' in session
    user_id = session.get('user_id')
    
    # Get affiliate info if user is logged in and is an affiliate
    affiliate = None
    if user_is_logged_in:
        affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    
    return render_template(
        'affiliate/terms.html',
        affiliate=affiliate,
        user_is_logged_in=user_is_logged_in
    )

@affiliate_bp.route('/tell-a-friend')
def tell_a_friend():
    """Affiliate referral tools page"""
    # Import database models inside function to avoid circular imports
    from database import User, Affiliate, db
    
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to access your affiliate tools', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get user's affiliate info
    affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    
    if not affiliate:
        # User is not an affiliate yet, redirect to registration
        flash('Please register as an affiliate first', 'info')
        return redirect(url_for('affiliate.register'))
    
    # Generate referral URL
    base_url = request.host_url.rstrip('/')
    referral_url = f"{base_url}/?ref={affiliate.referral_code}"
    
    # Generate email template
    email_template = f"""
    Hey there,

    I've been using this amazing AI chat platform called GloriaMundo, and I thought you might like it too.
    
    It's like ChatGPT but with some really cool features like document processing, image handling, and it has access to a wide range of AI models.
    
    You can try it out here: {referral_url}
    
    Let me know what you think!
    
    Best,
    [Your Name]
    """
    
    # Generate social media templates
    twitter_template = f"I've been using GloriaMundo AI for my daily tasks and research, and it's a game-changer! Try it out: {referral_url} #AI #ChatGPT #ProductivityTools"
    
    facebook_template = f"""
    I recently discovered GloriaMundo AI, and it's been a game-changer for my productivity!
    
    It's like having a super-smart assistant that can help with research, writing, learning, and more. You can upload documents, images, and have natural conversations.
    
    Check it out if you're looking to level up your AI tools: {referral_url}
    """
    
    linkedin_template = f"""
    🤖 AI Tool Recommendation 🤖
    
    I've been using GloriaMundo AI for [specific use case], and it's been incredibly helpful.
    
    What sets it apart from other AI assistants:
    ✅ Document processing
    ✅ Image analysis
    ✅ Access to multiple AI models
    ✅ Long-term memory
    
    If you're looking to boost your productivity with AI, I recommend giving it a try: {referral_url}
    
    #ArtificialIntelligence #ProductivityTools #AIAssistant
    """
    
    return render_template(
        'affiliate/tell_a_friend.html',
        affiliate=affiliate,
        referral_url=referral_url,
        email_template=email_template,
        twitter_template=twitter_template,
        facebook_template=facebook_template,
        linkedin_template=linkedin_template
    )

@affiliate_bp.route('/commissions')
def commissions():
    """View affiliate commissions"""
    # Import database models inside function to avoid circular imports
    from database import User, Affiliate, Commission, db
    
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to view your commissions', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get user's affiliate info
    affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    
    if not affiliate:
        # User is not an affiliate yet, redirect to registration
        flash('Please register as an affiliate first', 'info')
        return redirect(url_for('affiliate.register'))
    
    # Get affiliate commissions
    commissions = Commission.query.filter_by(affiliate_id=affiliate.id).order_by(Commission.created_at.desc()).all()
    
    # Calculate totals
    total_earned = sum(c.commission_amount for c in commissions if c.status in ['approved', 'paid'])
    total_pending = sum(c.commission_amount for c in commissions if c.status in ['pending', 'ready'])
    total_ready = sum(c.commission_amount for c in commissions if c.status == 'ready')
    
    return render_template(
        'affiliate/commissions.html',
        affiliate=affiliate,
        commissions=commissions,
        total_earned=total_earned,
        total_pending=total_pending,
        total_ready=total_ready
    )

@affiliate_bp.route('/api/track-referral', methods=['POST'])
def track_referral():
    """API endpoint to track affiliate referrals"""
    # Import database models inside function to avoid circular imports
    from database import Affiliate, CustomerReferral, db
    
    try:
        data = request.get_json()
        referral_code = data.get('referral_code')
        referral_source = data.get('source', 'direct')
        
        if not referral_code:
            return jsonify({'success': False, 'error': 'Missing referral code'}), 400
        
        # Look up affiliate by referral code
        affiliate = Affiliate.query.filter_by(referral_code=referral_code).first()
        
        if not affiliate:
            return jsonify({'success': False, 'error': 'Invalid referral code'}), 404
        
        # Generate a cookie value to track this referral
        cookie_value = str(uuid.uuid4())
        
        # Create referral record
        referral = CustomerReferral(
            affiliate_id=affiliate.id,
            referral_code=referral_code,
            referral_source=referral_source,
            cookie_value=cookie_value,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            converted=False,
            created_at=datetime.now()
        )
        
        db.session.add(referral)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'referral_id': referral.id,
            'cookie_value': cookie_value,
            'expiry': (datetime.now() + timedelta(days=30)).isoformat()
        })
    except Exception as e:
        logger.error(f"Error tracking referral: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@affiliate_bp.route('/api/commission-metrics', methods=['GET'])
def commission_metrics():
    """API endpoint to get commission metrics for charts"""
    # Import database models inside function to avoid circular imports
    from database import User, Affiliate, Commission, db
    
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    
    # Get user's affiliate info
    affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    
    if not affiliate:
        return jsonify({'success': False, 'error': 'Not an affiliate'}), 403
    
    # Get affiliate commissions
    commissions = Commission.query.filter_by(affiliate_id=affiliate.id).order_by(Commission.created_at.desc()).all()
    
    # Calculate earnings by month (for chart)
    monthly_data = {}
    for commission in commissions:
        if commission.status in ['approved', 'paid']:
            month_key = commission.created_at.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = 0
            monthly_data[month_key] += commission.commission_amount
    
    # Ensure at least 6 months of data for the chart
    chart_data = []
    today = datetime.now()
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_key = month_date.strftime('%Y-%m')
        month_label = month_date.strftime('%b %Y')
        chart_data.append({
            'month': month_label,
            'amount': monthly_data.get(month_key, 0)
        })
    
    return jsonify({
        'success': True,
        'data': chart_data
    })

@affiliate_bp.route('/agree-to-terms', methods=['POST'])
def agree_to_terms():
    """Handle affiliate agreement to terms submission"""
    # Import database models inside function to avoid circular imports
    from database import User, Affiliate, db
    
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to continue', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get user's affiliate info
    affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    
    if not affiliate:
        flash('You must be registered as an affiliate first', 'error')
        return redirect(url_for('affiliate.register'))
    
    # Mark terms as agreed by setting the timestamp
    affiliate.terms_agreed_at = datetime.now()
    
    # Update status to active once terms are agreed
    affiliate.status = 'active'
    
    try:
        db.session.commit()
        flash('Thank you for agreeing to the affiliate terms!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating terms agreement: {str(e)}")
        flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('affiliate.dashboard'))

@affiliate_bp.route('/update-paypal-email', methods=['POST'])
def update_paypal_email():
    """Update affiliate's PayPal email address"""
    # Import database models inside function to avoid circular imports
    from app import db
    from models import User, Affiliate
    from flask_login import login_required, current_user
    
    # Check if user is logged in via flask_login
    # This explicitly handles the login check before processing
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    # Get user's affiliate info
    affiliate = Affiliate.query.filter_by(email=current_user.email).first()
    
    if not affiliate:
        flash('You must be an affiliate to update your PayPal email', 'error')
        return redirect(url_for('billing.account_management'))
    
    # Get and validate new email
    paypal_email = request.form.get('paypal_email', '').strip()
    
    if not paypal_email:
        flash('PayPal email is required', 'error')
        return redirect(url_for('billing.account_management'))
    
    # Update the affiliate's PayPal email
    try:
        affiliate.paypal_email = paypal_email
        # Only update the timestamp field if it exists
        if hasattr(affiliate, 'updated_at'):
            affiliate.updated_at = datetime.now()
        db.session.commit()
        flash('PayPal email updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating PayPal email: {str(e)}", exc_info=True)
        flash(f'An error occurred: {str(e)}', 'error')
    
    # Redirect back to account management page
    return redirect(url_for('billing.account_management'))

# Helper function for templates
def affiliate_helpers():
    """Provide helper functions to affiliate templates"""
    def format_date(date):
        """Format a date for display"""
        if not date:
            return ''
        if isinstance(date, str):
            try:
                date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            except ValueError:
                return date
        return date.strftime('%Y-%m-%d %H:%M')
    
    def format_currency(amount):
        """Format an amount as currency"""
        if amount is None:
            return '$0.00'
        return f'${amount:.2f}'
    
    def get_status_class(status):
        """Get CSS class for status display"""
        status_classes = {
            'pending': 'bg-blue-100 text-blue-800',
            'ready': 'bg-yellow-100 text-yellow-800',
            'approved': 'bg-green-100 text-green-800',
            'paid': 'bg-purple-100 text-purple-800',
            'rejected': 'bg-red-100 text-red-800',
            'cancelled': 'bg-gray-100 text-gray-800',
            'converted': 'bg-green-100 text-green-800'
        }
        return status_classes.get(status, 'bg-gray-100 text-gray-800')
    
    return {
        'format_affiliate_date': format_date,
        'format_affiliate_currency': format_currency,
        'get_affiliate_status_class': get_status_class
    }

def init_app(app):
    """
    Initialize the affiliate blueprint with a Flask application
    
    This function registers the affiliate blueprint and adds its context processors.
    It carefully avoids circular imports and re-registration issues.
    
    Args:
        app: Flask application
        
    Returns:
        None
    """
    try:
        # Register the context processor first
        app.context_processor(affiliate_helpers)
        
        # Then register the blueprint
        app.register_blueprint(affiliate_bp)
        
        logger.info("Affiliate blueprint initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing affiliate blueprint: {e}")