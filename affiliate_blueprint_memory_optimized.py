"""
Affiliate Blueprint Module (Memory Optimized Version)

This module provides a Flask blueprint for the affiliate system.
This implementation resolves circular import issues, prevents memory leaks,
and optimizes database queries for better performance.
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
        # Auto-create an affiliate account
        try:
            # Get user data
            user = User.query.get(user_id)
            if not user:
                flash('User not found', 'error')
                return redirect(url_for('billing.account_management'))
                
            # Generate a unique referral code
            referral_code = str(uuid.uuid4())[:8]
            
            # Create new affiliate record
            affiliate = Affiliate(
                user_id=user_id,
                name=user.username,
                email=user.email,
                referral_code=referral_code,
                status='active',
                terms_agreed_at=datetime.now()
            )
            db.session.add(affiliate)
            db.session.commit()
            logger.info(f"Auto-created affiliate account for user {user_id} during dashboard access")
            flash('You have been automatically registered as an affiliate!', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error auto-creating affiliate: {str(e)}", exc_info=True)
            flash('There was a problem creating your affiliate account. Please try again.', 'error')
            return redirect(url_for('billing.account_management'))
    
    # Get affiliate commissions (limited to most recent 50 for dashboard display)
    commissions = Commission.query.filter_by(affiliate_id=affiliate.id).order_by(Commission.created_at.desc()).limit(50).all()
    
    # Get referrals (limited to most recent 50 for dashboard display)
    referrals = CustomerReferral.query.filter_by(affiliate_id=affiliate.id).order_by(CustomerReferral.created_at.desc()).limit(50).all()
    
    # For calculating totals, use aggregation directly at the database level
    # This avoids loading all records into memory
    total_earned_result = db.session.query(db.func.sum(Commission.commission_amount)).filter(
        Commission.affiliate_id == affiliate.id,
        Commission.status.in_(['approved', 'paid'])
    ).scalar()
    total_earned = total_earned_result or 0
    
    total_pending_result = db.session.query(db.func.sum(Commission.commission_amount)).filter(
        Commission.affiliate_id == affiliate.id,
        Commission.status.in_(['pending', 'ready'])
    ).scalar()
    total_pending = total_pending_result or 0
    
    # Count the total number of referrals
    total_referrals = CustomerReferral.query.filter_by(affiliate_id=affiliate.id).count()
    
    # Count conversions
    total_conversions = CustomerReferral.query.filter_by(
        affiliate_id=affiliate.id, 
        converted=True
    ).count()
    
    conversion_rate = (total_conversions / total_referrals * 100) if total_referrals > 0 else 0
    
    # Calculate earnings by month (for chart) - again using aggregation at DB level
    # Get the date 6 months ago
    six_months_ago = datetime.now() - timedelta(days=180)
    
    # Query for monthly earnings for the past 6 months
    monthly_earnings = db.session.query(
        db.func.date_trunc('month', Commission.created_at).label('month'),
        db.func.sum(Commission.commission_amount).label('amount')
    ).filter(
        Commission.affiliate_id == affiliate.id,
        Commission.status.in_(['approved', 'paid']),
        Commission.created_at >= six_months_ago
    ).group_by(
        db.func.date_trunc('month', Commission.created_at)
    ).all()
    
    # Convert to dictionary for easy lookup
    monthly_data = {
        month.strftime('%Y-%m'): float(amount) 
        for month, amount in monthly_earnings
    }
    
    # Ensure 6 months of data
    months = []
    values = []
    today = datetime.now()
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_key = month_date.strftime('%Y-%m')
        month_label = month_date.strftime('%b %Y')
        months.append(month_label)
        values.append(monthly_data.get(month_key, 0))
    
    # Get recent activity - limit to 10 most recent items
    recent_activity = []
    
    # Add commissions to activity - only the few most recent
    for commission in commissions[:5]:
        activity = {
            'type': 'commission',
            'date': commission.created_at,
            'amount': f'${commission.commission_amount:.2f}',
            'status': commission.status,
            'description': f'Commission from purchase (Level {commission.commission_level})'
        }
        recent_activity.append(activity)
    
    # Add referrals to activity - only the few most recent
    for referral in referrals[:5]:
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
    """
    Auto-creates an affiliate record for the user and redirects to dashboard.
    This is a compatibility route that now automatically creates active affiliates.
    """
    # Import database models inside function to avoid circular imports
    from database import User, Affiliate, db
    
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to access your affiliate dashboard', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # Check if user is already an affiliate
    existing_affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    if existing_affiliate:
        # If they already have an affiliate record, ensure it's active
        if existing_affiliate.status != 'active':
            existing_affiliate.status = 'active'
            existing_affiliate.terms_agreed_at = datetime.now()
            try:
                db.session.commit()
                flash('Your affiliate account has been activated!', 'success')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error activating affiliate: {str(e)}")
        
        # Redirect to dashboard
        return redirect(url_for('affiliate.dashboard'))
    
    # Auto-create active affiliate for user
    try:
        # Generate a unique referral code
        referral_code = str(uuid.uuid4())[:8]
        
        # Create new affiliate
        affiliate = Affiliate(
            user_id=user_id,
            name=user.username,
            email=user.email,
            referral_code=referral_code,
            status='active',
            terms_agreed_at=datetime.now()
        )
        
        db.session.add(affiliate)
        db.session.commit()
        flash('Your affiliate account has been activated!', 'success')
        return redirect(url_for('affiliate.dashboard'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error auto-creating affiliate: {str(e)}")
        flash('An error occurred while setting up your affiliate account. Please try again.', 'error')
        return redirect(url_for('billing.account_management'))

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
        # Auto-create an affiliate account
        try:
            # Get user data
            user = User.query.get(user_id)
            if not user:
                flash('User not found', 'error')
                return redirect(url_for('billing.account_management'))
                
            # Generate a unique referral code
            referral_code = str(uuid.uuid4())[:8]
            
            # Create new affiliate record
            affiliate = Affiliate(
                user_id=user_id,
                name=user.username,
                email=user.email,
                referral_code=referral_code,
                status='active',
                terms_agreed_at=datetime.now()
            )
            db.session.add(affiliate)
            db.session.commit()
            logger.info(f"Auto-created affiliate account for user {user_id} during tell-a-friend access")
            flash('You have been automatically registered as an affiliate!', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error auto-creating affiliate: {str(e)}", exc_info=True)
            flash('There was a problem setting up your affiliate account. Please try again.', 'error')
            return redirect(url_for('billing.account_management'))
    
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
        # Auto-create an affiliate account
        try:
            # Get user data
            user = User.query.get(user_id)
            if not user:
                flash('User not found', 'error')
                return redirect(url_for('billing.account_management'))
                
            # Generate a unique referral code
            referral_code = str(uuid.uuid4())[:8]
            
            # Create new affiliate record
            affiliate = Affiliate(
                user_id=user_id,
                name=user.username,
                email=user.email,
                referral_code=referral_code,
                status='active',
                terms_agreed_at=datetime.now()
            )
            db.session.add(affiliate)
            db.session.commit()
            logger.info(f"Auto-created affiliate account for user {user_id} during commissions view")
            flash('You have been automatically registered as an affiliate!', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error auto-creating affiliate: {str(e)}", exc_info=True)
            flash('There was a problem setting up your affiliate account. Please try again.', 'error')
            return redirect(url_for('billing.account_management'))
    
    # Get affiliate commissions (limited to most recent 50 for performance)
    commissions = Commission.query.filter_by(affiliate_id=affiliate.id).order_by(Commission.created_at.desc()).limit(50).all()
    
    # Calculate totals using direct database aggregation instead of loading all records
    total_earned_result = db.session.query(db.func.sum(Commission.commission_amount)).filter(
        Commission.affiliate_id == affiliate.id,
        Commission.status.in_(['approved', 'paid'])
    ).scalar()
    total_earned = total_earned_result or 0
    
    total_pending_result = db.session.query(db.func.sum(Commission.commission_amount)).filter(
        Commission.affiliate_id == affiliate.id,
        Commission.status.in_(['pending', 'ready'])
    ).scalar()
    total_pending = total_pending_result or 0
    
    total_ready_result = db.session.query(db.func.sum(Commission.commission_amount)).filter(
        Commission.affiliate_id == affiliate.id,
        Commission.status == 'ready'
    ).scalar()
    total_ready = total_ready_result or 0
    
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
    
    # Use aggregation directly at DB level to avoid memory issues
    six_months_ago = datetime.now() - timedelta(days=180)
    
    # Query for monthly earnings for the past 6 months
    monthly_earnings = db.session.query(
        db.func.date_trunc('month', Commission.created_at).label('month'),
        db.func.sum(Commission.commission_amount).label('amount')
    ).filter(
        Commission.affiliate_id == affiliate.id,
        Commission.status.in_(['approved', 'paid']),
        Commission.created_at >= six_months_ago
    ).group_by(
        db.func.date_trunc('month', Commission.created_at)
    ).all()
    
    # Convert to dictionary for easy lookup
    monthly_data = {
        month.strftime('%Y-%m'): float(amount) 
        for month, amount in monthly_earnings
    }
    
    # Ensure 6 months of data
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
def agree_to_terms_handler():
    """
    Handle the submission of the affiliate terms agreement form
    
    This is now simplified to automatically create or activate an affiliate account
    and just update the PayPal email if provided. No terms agreement is required.
    """
    # Import database models inside function to avoid circular imports
    from database import User, Affiliate, db
    
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to continue', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # Get PayPal email from form
    paypal_email = request.form.get('paypal_email', '').strip()
    
    # Check if user is already an affiliate
    existing_affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    
    try:
        if existing_affiliate:
            # Update existing affiliate
            existing_affiliate.status = 'active'
            if paypal_email:
                existing_affiliate.paypal_email = paypal_email
            existing_affiliate.terms_agreed_at = datetime.now()
            logger.info(f"Updated existing affiliate record for user {user_id} with status 'active'")
            flash('Your affiliate account has been updated!', 'success')
        else:
            # Generate a unique referral code
            referral_code = str(uuid.uuid4())[:8]
            
            # Create new affiliate
            affiliate = Affiliate(
                user_id=user_id,
                name=user.username,
                email=user.email,
                referral_code=referral_code,
                status='active',
                terms_agreed_at=datetime.now()
            )
            if paypal_email:
                affiliate.paypal_email = paypal_email
            
            db.session.add(affiliate)
            logger.info(f"Created new active affiliate record for user {user_id}")
            flash('You are now registered as an affiliate!', 'success')
        
        # Commit the changes
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing affiliate request: {str(e)}", exc_info=True)
        flash('An error occurred while processing your request. Please try again.', 'error')
    
    # Redirect to the Tell a Friend tab
    return redirect(url_for('billing.account_management') + '#tellFriend')

@affiliate_bp.route('/update-paypal-email', methods=['POST'])
def update_paypal_email():
    """Update affiliate's PayPal email address"""
    # Import database models inside function to avoid circular imports
    from database import db, User, Affiliate
    
    # Check if user is logged in via session
    if 'user_id' not in session:
        flash('Please login to update your PayPal email', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # Get user's affiliate info by matching user ID
    affiliate = Affiliate.query.filter_by(user_id=user_id).first()
    
    # If not found by user_id, try by email
    if not affiliate:
        affiliate = Affiliate.query.filter_by(email=user.email).first()
    
    if not affiliate:
        # If no affiliate is found, create one automatically
        logger.info(f"Creating affiliate record for user {user_id} during PayPal email update")
        referral_code = str(uuid.uuid4())[:8]
        
        affiliate = Affiliate(
            user_id=user_id,  # Include user_id here
            name=user.username,
            email=user.email,
            referral_code=referral_code,
            status='active',
            terms_agreed_at=datetime.now()
        )
        db.session.add(affiliate)
        
    # Get and validate new email
    paypal_email = request.form.get('paypal_email', '').strip()
    
    if not paypal_email:
        flash('PayPal email is required', 'error')
        return redirect(url_for('billing.account_management') + '#tellFriend')
    
    # Update the affiliate's PayPal email
    try:
        # Log the update for debugging
        logger.info(f"Updating PayPal email for affiliate {affiliate.id} to {paypal_email}")
        
        affiliate.paypal_email = paypal_email
        
        # Update timestamp
        if hasattr(affiliate, 'updated_at'):
            affiliate.updated_at = datetime.now()
            
        db.session.commit()
        flash('PayPal email updated successfully', 'success')
        logger.info(f"Successfully updated PayPal email for affiliate {affiliate.id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating PayPal email: {str(e)}", exc_info=True)
        flash('An error occurred while updating your PayPal email. Please try again.', 'error')
    
    # Redirect back to account management page, specifically the Tell a Friend tab
    return redirect(url_for('billing.account_management') + '#tellFriend')

# Helper function for templates
def affiliate_helpers():
    """Provide helper functions to affiliate templates"""
    def format_date(date):
        """Format a date for display"""
        if not date:
            return ''
        return date.strftime('%Y-%m-%d %H:%M')
    
    def format_currency(amount):
        """Format an amount as currency"""
        return f'${amount:.2f}'
    
    def get_status_class(status):
        """Get CSS class for status display"""
        status_classes = {
            'pending': 'text-warning',
            'ready': 'text-info',
            'approved': 'text-success',
            'paid': 'text-primary',
            'rejected': 'text-danger'
        }
        return status_classes.get(status, '')
    
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
    # Only register the blueprint if it hasn't been registered yet
    if not app.blueprints.get('affiliate'):
        # Register blueprint
        app.register_blueprint(affiliate_bp)
        
        # Add template context processor for helper functions
        app.context_processor(affiliate_helpers)
        
        logger.info("Affiliate blueprint registered successfully")
    else:
        logger.info("Affiliate blueprint already registered, skipping")