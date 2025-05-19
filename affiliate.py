"""
Affiliate Module for GloriaMundo Chatbot (Fixed)

This module handles affiliate routes, registration, commission tracking,
and PayPal payouts for the two-tier affiliate system.

This version resolves circular import issues and implements improved
Redis connection handling for better resilience.
"""

import os
import logging
from datetime import datetime, timedelta
import stripe
import json
from urllib.parse import urljoin

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify, abort, g
from flask_login import current_user, login_required
from sqlalchemy import desc, func, and_, not_
from flask_wtf.csrf import validate_csrf
from werkzeug.security import generate_password_hash

# Import Redis helper modules for improved connection handling
from redis_helper import check_redis_connection, configure_redis

# Create blueprint
affiliate_bp = Blueprint('affiliate', __name__, url_prefix='/affiliate', template_folder='templates')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define helper functions that will be available to templates
def affiliate_helpers():
    """Provide helper functions to affiliate templates"""
    return {
        'format_date': lambda dt: dt.strftime('%Y-%m-%d %H:%M') if dt else 'N/A',
        'format_currency': lambda amount: f"${amount:.2f}" if amount else '$0.00',
        'commission_status_class': lambda status: {
            'pending': 'bg-yellow-100 text-yellow-800',
            'approved': 'bg-green-100 text-green-800',
            'rejected': 'bg-red-100 text-red-800',
            'paid': 'bg-blue-100 text-blue-800'
        }.get(status.lower(), 'bg-gray-100 text-gray-800')
    }

def init_app(app):
    """
    Initialize the affiliate blueprint with a Flask application
    
    Args:
        app: Flask application
        
    Returns:
        None
    """
    try:
        # First register the blueprint
        app.register_blueprint(affiliate_bp)
        
        # Then add template helpers to the app directly
        app.context_processor(affiliate_helpers)
        
        # Import database models here to avoid circular imports
        from database import db, User, Affiliate, Commission, Transaction, CustomerReferral
        
        # Define route handlers within the init_app function to avoid circular imports
        # but still have access to the database models
        
        @affiliate_bp.route('/')
        @login_required
        def dashboard():
            """Affiliate dashboard view"""
            # Check if user is an affiliate
            affiliate = Affiliate.query.filter_by(user_id=current_user.id).first()
            
            if not affiliate:
                return redirect(url_for('affiliate.register'))
                
            # Get account stats
            total_referrals = CustomerReferral.query.filter_by(affiliate_id=affiliate.id).count()
            total_commissions = Commission.query.filter_by(affiliate_id=affiliate.id).count()
            total_earnings = db.session.query(func.sum(Commission.commission_amount)) \
                .filter(Commission.affiliate_id == affiliate.id) \
                .filter(Commission.status.in_(['approved', 'paid'])) \
                .scalar() or 0
                
            # Get recent commissions (limit to 10)
            recent_commissions = Commission.query \
                .filter_by(affiliate_id=affiliate.id) \
                .order_by(desc(Commission.created_at)) \
                .limit(10) \
                .all()
                
            # Get recent referrals (limit to 10)
            recent_referrals = CustomerReferral.query \
                .filter_by(affiliate_id=affiliate.id) \
                .order_by(desc(CustomerReferral.created_at)) \
                .limit(10) \
                .all()
                
            return render_template(
                'affiliate/dashboard.html',
                affiliate=affiliate,
                stats={
                    'total_referrals': total_referrals,
                    'total_commissions': total_commissions,
                    'total_earnings': total_earnings
                },
                recent_commissions=recent_commissions,
                recent_referrals=recent_referrals
            )
            
        @affiliate_bp.route('/register', methods=['GET', 'POST'])
        @login_required
        def register():
            """Register as an affiliate"""
            # Check if user is already an affiliate
            existing_affiliate = Affiliate.query.filter_by(user_id=current_user.id).first()
            if existing_affiliate:
                flash('You are already registered as an affiliate', 'info')
                return redirect(url_for('affiliate.dashboard'))
                
            if request.method == 'POST':
                try:
                    # Validate CSRF token
                    csrf_token = request.form.get('csrf_token')
                    if not csrf_token or not validate_csrf(csrf_token):
                        flash('Invalid CSRF token', 'error')
                        return redirect(url_for('affiliate.register'))
                        
                    # Get form data
                    name = request.form.get('name')
                    email = request.form.get('email')
                    paypal_email = request.form.get('paypal_email')
                    website = request.form.get('website')
                    terms_agreed = request.form.get('terms_agreed') == 'on'
                    
                    # Validate form data
                    if not name or not email or not paypal_email:
                        flash('Please fill out all required fields', 'error')
                        return redirect(url_for('affiliate.register'))
                        
                    if not terms_agreed:
                        flash('You must agree to the terms and conditions', 'error')
                        return redirect(url_for('affiliate.register'))
                        
                    # Generate referral code (based on username and random string)
                    import string
                    import random
                    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                    referral_code = f"{current_user.username.lower()}-{random_str}"
                    
                    # Create affiliate record
                    affiliate = Affiliate(
                        user_id=current_user.id,
                        name=name,
                        email=email,
                        paypal_email=paypal_email,
                        website=website,
                        referral_code=referral_code,
                        status='active',
                        terms_agreed_at=datetime.utcnow()
                    )
                    
                    db.session.add(affiliate)
                    db.session.commit()
                    
                    flash('You are now registered as an affiliate!', 'success')
                    return redirect(url_for('affiliate.dashboard'))
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error registering affiliate: {str(e)}")
                    flash('An error occurred during registration. Please try again.', 'error')
                    
            # GET request or form validation failed
            return render_template('affiliate/register.html')
            
        @affiliate_bp.route('/tell-a-friend')
        @login_required
        def tell_a_friend():
            """Affiliate referral tools page"""
            # Check if user is an affiliate
            affiliate = Affiliate.query.filter_by(user_id=current_user.id).first()
            
            if not affiliate:
                flash('You need to register as an affiliate first', 'warning')
                return redirect(url_for('affiliate.register'))
                
            # Generate referral URL
            base_url = request.host_url.rstrip('/')
            referral_url = f"{base_url}/?ref={affiliate.referral_code}"
            
            # Get referral stats
            total_referrals = CustomerReferral.query.filter_by(affiliate_id=affiliate.id).count()
            successful_referrals = CustomerReferral.query \
                .filter_by(affiliate_id=affiliate.id) \
                .filter(CustomerReferral.converted_at.isnot(None)) \
                .count()
                
            return render_template(
                'affiliate/tell_a_friend.html',
                affiliate=affiliate,
                referral_url=referral_url,
                stats={
                    'total_referrals': total_referrals,
                    'successful_referrals': successful_referrals,
                    'conversion_rate': (successful_referrals / total_referrals * 100) if total_referrals > 0 else 0
                }
            )
            
        @affiliate_bp.route('/commissions')
        @login_required
        def commissions():
            """View affiliate commissions"""
            # Check if user is an affiliate
            affiliate = Affiliate.query.filter_by(user_id=current_user.id).first()
            
            if not affiliate:
                flash('You need to register as an affiliate first', 'warning')
                return redirect(url_for('affiliate.register'))
                
            # Get commissions with pagination
            page = request.args.get('page', 1, type=int)
            per_page = 20
            
            commissions_query = Commission.query \
                .filter_by(affiliate_id=affiliate.id) \
                .order_by(desc(Commission.created_at))
                
            # Apply status filter if provided
            status_filter = request.args.get('status')
            if status_filter and status_filter != 'all':
                commissions_query = commissions_query.filter_by(status=status_filter)
                
            # Get paginated results
            pagination = commissions_query.paginate(page=page, per_page=per_page)
            commissions_list = pagination.items
            
            # Get commission stats
            total_earnings = db.session.query(func.sum(Commission.commission_amount)) \
                .filter(Commission.affiliate_id == affiliate.id) \
                .filter(Commission.status.in_(['approved', 'paid'])) \
                .scalar() or 0
                
            pending_earnings = db.session.query(func.sum(Commission.commission_amount)) \
                .filter(Commission.affiliate_id == affiliate.id) \
                .filter(Commission.status == 'pending') \
                .scalar() or 0
                
            return render_template(
                'affiliate/commissions.html',
                affiliate=affiliate,
                commissions=commissions_list,
                pagination=pagination,
                stats={
                    'total_earnings': total_earnings,
                    'pending_earnings': pending_earnings
                },
                active_status=status_filter or 'all'
            )
            
        @affiliate_bp.route('/api/track-referral', methods=['POST'])
        def track_referral():
            """API endpoint to track affiliate referrals"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'Invalid request data'}), 400
                    
                referral_code = data.get('referral_code')
                if not referral_code:
                    return jsonify({'success': False, 'error': 'Missing referral code'}), 400
                    
                # Look up affiliate by referral code
                affiliate = Affiliate.query.filter_by(referral_code=referral_code, status='active').first()
                if not affiliate:
                    return jsonify({'success': False, 'error': 'Invalid referral code'}), 404
                    
                # Get or create visitor ID from session or generate new one
                visitor_id = session.get('visitor_id')
                if not visitor_id:
                    import uuid
                    visitor_id = str(uuid.uuid4())
                    session['visitor_id'] = visitor_id
                    
                # Check if this visitor was already referred
                existing_referral = CustomerReferral.query.filter_by(visitor_id=visitor_id).first()
                if existing_referral:
                    # Update last seen time but don't create a new referral
                    existing_referral.last_seen_at = datetime.utcnow()
                    db.session.commit()
                    return jsonify({'success': True, 'message': 'Existing referral updated'})
                    
                # Create new referral record
                referral = CustomerReferral(
                    affiliate_id=affiliate.id,
                    visitor_id=visitor_id,
                    referral_code=referral_code,
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string,
                    landing_page=data.get('landing_page', '/'),
                    created_at=datetime.utcnow(),
                    last_seen_at=datetime.utcnow()
                )
                
                db.session.add(referral)
                db.session.commit()
                
                return jsonify({'success': True, 'message': 'Referral tracked successfully'})
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error tracking referral: {str(e)}")
                return jsonify({'success': False, 'error': 'Server error'}), 500
                
        @affiliate_bp.route('/api/commission-metrics')
        @login_required
        def commission_metrics():
            """API endpoint to get commission metrics for charts"""
            # Check if user is an affiliate
            affiliate = Affiliate.query.filter_by(user_id=current_user.id).first()
            
            if not affiliate:
                return jsonify({'success': False, 'error': 'Not an affiliate'}), 403
                
            # Get time range from query parameters (default to last 30 days)
            days = request.args.get('days', 30, type=int)
            if days not in [7, 30, 90, 365]:
                days = 30
                
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get daily commission totals
            daily_totals = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                
                # Query commissions for this day
                day_total = db.session.query(func.sum(Commission.commission_amount)) \
                    .filter(Commission.affiliate_id == affiliate.id) \
                    .filter(Commission.created_at >= current_date) \
                    .filter(Commission.created_at < next_date) \
                    .scalar() or 0
                    
                daily_totals.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'amount': float(day_total)
                })
                
                current_date = next_date
                
            # Get commission status breakdown
            status_breakdown = []
            for status in ['pending', 'approved', 'paid', 'rejected']:
                count = Commission.query \
                    .filter_by(affiliate_id=affiliate.id, status=status) \
                    .count()
                    
                amount = db.session.query(func.sum(Commission.commission_amount)) \
                    .filter(Commission.affiliate_id == affiliate.id) \
                    .filter(Commission.status == status) \
                    .scalar() or 0
                    
                status_breakdown.append({
                    'status': status,
                    'count': count,
                    'amount': float(amount)
                })
                
            return jsonify({
                'success': True,
                'daily_totals': daily_totals,
                'status_breakdown': status_breakdown
            })
        @affiliate_bp.route('/update-paypal-email', methods=['POST'])
        @login_required
        def update_paypal_email():
            """Update affiliate's PayPal email address"""
            try:
                # Get the affiliate record for the current user
                # Instead of looking up by user_id, find by email for better compatibility
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
                affiliate.paypal_email = paypal_email
                
                # Check if updated_at field exists before trying to set it
                if hasattr(affiliate, 'updated_at'):
                    affiliate.updated_at = datetime.now()
                
                # Save changes to database
                db.session.commit()
                
                flash('PayPal email updated successfully', 'success')
                return redirect(url_for('billing.account_management'))
                
            except Exception as e:
                logger.error(f"Error updating PayPal email: {e}", exc_info=True)
                db.session.rollback()
                flash(f'An error occurred: {str(e)}', 'error')
                return redirect(url_for('billing.account_management'))
            
        logger.info("Affiliate blueprint initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing affiliate blueprint: {e}")