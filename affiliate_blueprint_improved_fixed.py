"""
Affiliate Blueprint Module (Improved and Fixed)

This module provides a Flask blueprint for the affiliate system.
This implementation resolves circular import issues and prevents the blueprint 
from being registered multiple times. It also fixes issues with PayPal email
updates and eliminates redirects to obsolete pages.
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
    from database import db
    from models import User, Commission, Transaction, CustomerReferral, AffiliateStatus
    
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to access your affiliate dashboard', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get user data
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('billing.account_management'))
    
    # Generate a referral code if the user doesn't have one
    if not user.referral_code:
        # Generate a unique referral code
        user.referral_code = str(uuid.uuid4())[:8]
        db.session.commit()
        logger.info(f"Auto-generated referral code for user {user_id}")
    
    # Get commissions directly from user object
    commissions = Commission.query.filter_by(user_id=user_id).order_by(Commission.created_at.desc()).all()
    
    # Get referrals
    referrals = CustomerReferral.query.filter_by(referrer_user_id=user_id).order_by(CustomerReferral.created_at.desc()).all()
    
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
        user=user,
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
    """
    Auto-creates an affiliate record for the user and redirects to dashboard.
    This is a compatibility route that now automatically creates active affiliates.
    """
    # Just redirect to dashboard, which will handle everything
    return redirect(url_for('affiliate.dashboard'))

@affiliate_bp.route('/tell-a-friend')
def tell_a_friend():
    """Affiliate referral tools page"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User
    
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to access your affiliate tools', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get user data
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('billing.account_management'))
    
    # Generate a referral code if the user doesn't have one
    if not user.referral_code:
        # Generate a unique referral code
        user.referral_code = str(uuid.uuid4())[:8]
        db.session.commit()
        logger.info(f"Auto-generated referral code for user {user_id} during tell-a-friend access")
    
    # Generate referral URL
    base_url = request.host_url.rstrip('/')
    referral_url = f"{base_url}/?ref={user.referral_code}"
    
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
        'affiliate/tell_friend_tab_simplified.html',
        user=user,
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
    from database import db
    from models import User, Commission
    
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to view your commissions', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get user data
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('billing.account_management'))
    
    # Generate a referral code if the user doesn't have one
    if not user.referral_code:
        # Generate a unique referral code
        user.referral_code = str(uuid.uuid4())[:8]
        db.session.commit()
        logger.info(f"Auto-generated referral code for user {user_id} during commissions view")
    
    # Get commissions
    commissions = Commission.query.filter_by(user_id=user_id).order_by(Commission.created_at.desc()).all()
    
    # Calculate totals
    total_earned = sum(c.commission_amount for c in commissions if c.status in ['approved', 'paid'])
    total_pending = sum(c.commission_amount for c in commissions if c.status in ['pending', 'ready'])
    total_ready = sum(c.commission_amount for c in commissions if c.status == 'ready')
    
    return render_template(
        'affiliate/commissions.html',
        user=user,
        commissions=commissions,
        total_earned=total_earned,
        total_pending=total_pending,
        total_ready=total_ready
    )

@affiliate_bp.route('/api/track-referral', methods=['POST'])
def track_referral():
    """API endpoint to track affiliate referrals"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User, CustomerReferral
    
    try:
        data = request.get_json()
        referral_code = data.get('referral_code')
        referral_source = data.get('source', 'direct')
        
        if not referral_code:
            return jsonify({'success': False, 'error': 'Missing referral code'}), 400
        
        # Look up user by referral code
        user = User.query.filter_by(referral_code=referral_code).first()
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid referral code'}), 404
        
        # Generate a cookie value to track this referral
        cookie_value = str(uuid.uuid4())
        
        # Create referral record
        referral = CustomerReferral(
            referrer_user_id=user.id,
            referral_code=referral_code,
            referral_source=referral_source,
            cookie_value=cookie_value,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            converted=False,
            created_at=datetime.now()
        )
        
        db.session.add(referral)
        db.session.commit()
        
        # Return cookie value for tracking
        return jsonify({
            'success': True,
            'cookie_value': cookie_value,
            'expires': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    except Exception as e:
        logger.error(f"Error tracking referral: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@affiliate_bp.route('/api/commission-metrics', methods=['GET'])
def commission_metrics():
    """API endpoint to get commission metrics for charts"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User, Commission
    
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    user_id = session['user_id']
    
    # Get commissions
    commissions = Commission.query.filter_by(user_id=user_id).all()
    
    # Group by month
    monthly_data = {}
    for commission in commissions:
        if commission.status in ['approved', 'paid']:
            month_key = commission.created_at.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = 0
            monthly_data[month_key] += commission.commission_amount
    
    # Prepare data for chart
    months = []
    values = []
    
    # Ensure at least 6 months of data for the chart
    today = datetime.now()
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_key = month_date.strftime('%Y-%m')
        month_label = month_date.strftime('%b %Y')
        months.append(month_label)
        values.append(monthly_data.get(month_key, 0))
    
    return jsonify({
        'success': True,
        'months': months,
        'values': values
    })

@affiliate_bp.route('/update-paypal-email', methods=['POST'])
def update_paypal_email():
    """Update affiliate's PayPal email address"""
    # Import database models inside function to avoid circular imports
    from database import db
    from models import User
    
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to update your PayPal email', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get form data
    paypal_email = request.form.get('paypal_email')
    
    if not paypal_email:
        flash('Please enter a valid PayPal email address', 'error')
        return redirect(url_for('billing.account_management'))
    
    # Update user's PayPal email
    try:
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('billing.account_management'))
        
        user.paypal_email = paypal_email
        db.session.commit()
        logger.info(f"Updated PayPal email for user {user_id}")
        flash('Your PayPal email has been updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating PayPal email: {str(e)}", exc_info=True)
        flash('There was a problem updating your PayPal email. Please try again.', 'error')
    
    return redirect(url_for('billing.account_management') + '#tellFriend')

def affiliate_helpers():
    """Provide helper functions to affiliate templates"""
    def format_date(date):
        """Format a date for display"""
        if not date:
            return ''
        return date.strftime('%b %d, %Y')
    
    def format_currency(amount):
        """Format an amount as currency"""
        if amount is None:
            return '$0.00'
        return f'${amount:.2f}'
    
    def get_status_class(status):
        """Get CSS class for status display"""
        status_classes = {
            'pending': 'text-warning',
            'ready': 'text-info',
            'approved': 'text-success',
            'paid': 'text-success',
            'rejected': 'text-danger',
            'cancelled': 'text-secondary'
        }
        return status_classes.get(status, 'text-secondary')
    
    return dict(
        format_date=format_date,
        format_currency=format_currency,
        get_status_class=get_status_class
    )

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
    # Only register if the blueprint is not already registered
    if 'affiliate' not in app.blueprints:
        app.register_blueprint(affiliate_bp)
        # Add context processor for affiliate templates
        app.context_processor(affiliate_helpers)
        
        logging.info("Affiliate blueprint registered")
    else:
        logging.info("Affiliate blueprint already registered, skipping")