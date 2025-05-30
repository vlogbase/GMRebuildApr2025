"""
Admin Module for GloriaMundo Chatbot

This module provides the admin routes for managing affiliates, commissions, and payouts.
It is completely independent of Flask-Admin to avoid template recursion issues.
"""

import os
import logging
import sys
import uuid
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, flash, redirect, url_for, render_template, request, abort, current_app, jsonify
from flask_login import current_user, login_required
from sqlalchemy import func, desc, and_, not_, text
from typing import NoReturn

from models import User, Transaction, Commission, CustomerReferral, CommissionStatus, AffiliateStatus, PaymentStatus, OpenRouterModel
from database import db

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# Create blueprint with unique name to avoid conflicts
admin_bp = Blueprint('admin_simple', __name__, url_prefix='/admin_simple')

# --- PayPal Integration Functions ---
def generate_sender_batch_id():
    """Generate a unique batch ID for PayPal payouts"""
    return f"GM_BATCH_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

def process_paypal_payout(sender_batch_id, payout_items):
    """
    Process PayPal payout (simplified stub implementation)
    
    In a real implementation, this would call the PayPal API.
    For now, we'll just return a simulated successful response.
    
    Args:
        sender_batch_id: A unique ID for this batch
        payout_items: List of payout items, each with recipient and amount
        
    Returns:
        dict: Simulated PayPal response
    """
    # Simulate a successful PayPal API response
    return {
        'batch_header': {
            'payout_batch_id': f'PAYPALREF_{sender_batch_id}',
            'batch_status': 'PENDING'
        }
    }

def check_payout_status(batch_id):
    """
    Check the status of a PayPal payout batch (simplified stub implementation)
    
    In a real implementation, this would call the PayPal API.
    For now, we'll just return a simulated response.
    
    Args:
        batch_id: The batch ID to check
        
    Returns:
        dict: Simulated PayPal response with batch status
    """
    # Simulate a PayPal API response
    # In reality, this would query the PayPal API for the actual status
    simulated_statuses = {
        'PENDING': 'The batch is pending processing.',
        'PROCESSING': 'The batch is being processed.',
        'SUCCESS': 'All payouts in the batch have been successfully processed.',
        'DENIED': 'The batch was denied.',
        'CANCELED': 'The batch was canceled.',
        'PARTIAL': 'Some payouts in the batch have been processed, some have failed.'
    }
    
    # For demo purposes, just return SUCCESS
    return {
        'batch_header': {
            'payout_batch_id': batch_id,
            'batch_status': 'SUCCESS',
            'time_completed': datetime.now().isoformat()
        },
        'items': [
            {
                'payout_item_id': f'{batch_id}_ITEM1',
                'transaction_status': 'SUCCESS',
                'payout_item_fee': {'currency': 'USD', 'value': '0.25'},
                'payout_batch_id': batch_id,
                'transaction_id': f'PAY-{uuid.uuid4().hex[:16]}'
            }
        ]
    }

# --- Admin Access Control ---
def is_admin():
    """Check if the current user is an admin (specifically andy@sentigral.com)"""
    return current_user.is_authenticated and current_user.email == 'andy@sentigral.com'

def admin_required(f):
    """Decorator to restrict access to admin users only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash('You do not have permission to access that page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Admin Routes ---
@admin_bp.route('/')
@admin_required
def index():
    """Admin dashboard with stats and KPIs"""
    logger.info("Admin dashboard route accessed")
    try:
        # Use timeout to prevent long-running queries
        timeout = 10  # seconds
        
        # Set a timeout context for the database session
        # This helps prevent worker timeouts and OOM errors
        from sqlalchemy.exc import OperationalError
        from sqlalchemy import text
        original_timeout = db.session.execute(text("SHOW statement_timeout")).scalar()
        db.session.execute(text(f"SET statement_timeout = {timeout * 1000}"))  # milliseconds
        
        try:
            # User stats - Use simplified queries with explicit columns to minimize memory usage
            logger.info("Getting user stats")
            total_users = db.session.query(func.count(User.id)).scalar() or 0
            
            # Get full User objects to avoid attribute setting issues
            recent_users = User.query.filter(User.created_at != None)\
            .order_by(User.created_at.desc())\
            .limit(5)\
            .all()
            
            # Affiliate stats (now using User table since all users are affiliates)
            logger.info("Getting affiliate stats")
            total_affiliates = db.session.query(func.count(User.id)).filter(User.referral_code != None).scalar() or 0
            # In our simplified system, all users with referral codes are considered active affiliates
            active_affiliates = total_affiliates
            
            # Commission stats
            logger.info("Getting commission stats")
            pending_commissions = db.session.query(func.count(Commission.id))\
                .filter_by(status=CommissionStatus.APPROVED.value)\
                .scalar() or 0
                
            # Get recent commissions (simplified to avoid relationship issues)
            recent_commissions = Commission.query.filter(Commission.created_at != None)\
            .order_by(Commission.created_at.desc())\
            .limit(5)\
            .all()
            
            # Revenue stats
            logger.info("Getting revenue stats")
            total_revenue = db.session.query(func.sum(Transaction.amount_usd))\
                .filter_by(status=PaymentStatus.COMPLETED.value)\
                .scalar() or 0
            
            # Use a smaller date range to reduce the amount of data processed
            logger.info("Preparing chart data")
            end_date = datetime.now()
            # Reducing from 30 to 14 days to minimize data processing
            start_date = end_date - timedelta(days=14)
            
            # Use optimized queries with date_trunc instead of func.date for better performance
            # User registrations by day (with null check to prevent errors)
            user_registrations = db.session.query(
                func.date_trunc('day', User.created_at).label('date'),
                func.count(User.id).label('count')
            ).filter(User.created_at != None, User.created_at >= start_date, User.created_at <= end_date)\
            .group_by(func.date_trunc('day', User.created_at))\
            .all()
            
            # Revenue by day (with null check to prevent errors)
            revenue_by_day = db.session.query(
                func.date_trunc('day', Transaction.created_at).label('date'),
                func.sum(Transaction.amount_usd).label('amount')
            ).filter(
                Transaction.created_at != None,
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date,
                Transaction.status == PaymentStatus.COMPLETED.value
            )\
            .group_by(func.date_trunc('day', Transaction.created_at))\
            .all()
            
            # Create a smaller date range (14 days instead of 30)
            date_range = [(start_date + timedelta(days=i)).date() for i in range(15)]  # 14 days + today
            
            # Create dict for fast lookups - handle datetime objects from date_trunc
            user_dict = {str(r[0].date() if r[0] else None): r[1] for r in user_registrations}
            revenue_dict = {str(r[0].date() if r[0] else None): float(r[1] or 0) for r in revenue_by_day}
            
            # Fill in missing dates with zeros
            user_data = [user_dict.get(str(d), 0) for d in date_range]
            revenue_data = [revenue_dict.get(str(d), 0) for d in date_range]
            date_labels = [d.strftime('%Y-%m-%d') for d in date_range]
            
            # Get PayPal mode
            paypal_mode = os.environ.get('PAYPAL_MODE', 'sandbox')
            
        finally:
            # Restore original timeout
            db.session.execute(text(f"SET statement_timeout = {original_timeout}"))
        
        logger.info("Rendering admin dashboard template")
        return render_template('admin/dashboard.html',
            total_users=total_users,
            recent_users=recent_users,
            total_affiliates=total_affiliates,
            active_affiliates=active_affiliates,
            pending_commissions=pending_commissions,
            recent_commissions=recent_commissions,
            total_revenue=total_revenue,
            user_labels=date_labels,
            user_data=user_data,
            revenue_labels=date_labels,
            revenue_data=revenue_data,
            paypal_mode=paypal_mode
        )
    except Exception as e:
        logger.error(f"Error in admin dashboard: {str(e)}", exc_info=True)
        # Simple fallback page in case of errors
        return f"""
        <html>
            <head><title>Admin Dashboard Error</title></head>
            <body>
                <h1>Error Loading Admin Dashboard</h1>
                <p>An error occurred while loading the admin dashboard: {str(e)}</p>
                <p>This has been logged for investigation.</p>
                <a href="/">Return to Home</a>
            </body>
        </html>
        """, 500

@admin_bp.route('/manage_commissions')
@admin_required
def manage_commissions():
    """Admin page for managing commissions"""
    try:
        # Set a timeout for this query to prevent long-running operations
        timeout = 10  # seconds
        from sqlalchemy.exc import OperationalError
        from sqlalchemy import text
        original_timeout = db.session.execute(text("SHOW statement_timeout")).scalar()
        db.session.execute(text(f"SET statement_timeout = {timeout * 1000}"))  # milliseconds
        
        try:
            logger.info("Accessing manage_commissions page")
            
            # Get aggregate totals for each affiliate rather than loading all commission records
            # This reduces memory usage significantly by letting the database do the aggregation
            affiliate_totals = db.session.query(
                Commission.affiliate_id,
                func.sum(Commission.commission_amount).filter(Commission.status == CommissionStatus.APPROVED.value).label('approved_total'),
                func.sum(Commission.commission_amount).filter(Commission.status == CommissionStatus.HELD.value).label('pending_total'),
                func.sum(Commission.commission_amount).filter(Commission.status == CommissionStatus.PAID.value).label('paid_total'),
                func.sum(Commission.commission_amount).filter(Commission.status == CommissionStatus.REJECTED.value).label('rejected_total'),
                func.count(Commission.id).label('commission_count')
            ).group_by(Commission.affiliate_id).all()
            
            # Get all affiliate info in a single query
            affiliate_ids = [t.affiliate_id for t in affiliate_totals]
            affiliates = {
                u.id: u for u in db.session.query(User).filter(User.id.in_(affiliate_ids)).all()
            } if affiliate_ids else {}
            
            # For affiliates with significant commission counts, load last 5 commissions
            # This prevents loading all commissions for affiliates with many records
            affiliate_recent_commissions = {}
            for total in affiliate_totals:
                if total.affiliate_id in affiliates:
                    # Only load up to 5 recent commissions per affiliate
                    recent = db.session.query(
                        Commission.id, 
                        Commission.affiliate_id,
                        Commission.commission_amount,
                        Commission.status,
                        Commission.created_at,
                        Commission.commission_level
                    ).filter(
                        Commission.affiliate_id == total.affiliate_id,
                        Commission.created_at != None
                    ).order_by(Commission.created_at.desc()).limit(5).all()
                    
                    affiliate_recent_commissions[total.affiliate_id] = recent
            
            # Build the affiliate_commissions structure but with optimized data
            affiliate_commissions = {}
            for total in affiliate_totals:
                affiliate_id = total.affiliate_id
                if affiliate_id in affiliates:
                    affiliate = affiliates[affiliate_id]
                    recent_commissions = affiliate_recent_commissions.get(affiliate_id, [])
                    
                    affiliate_commissions[affiliate_id] = {
                        'affiliate': affiliate,
                        'commissions': recent_commissions,  # Only the 5 most recent
                        'commission_count': total.commission_count,  # Total count for display
                        'approved_total': float(total.approved_total or 0),
                        'pending_total': float(total.pending_total or 0),
                        'paid_total': float(total.paid_total or 0),
                        'rejected_total': float(total.rejected_total or 0)
                    }
            
            # Sort affiliates by those with approved commissions first, then total amount
            sorted_affiliates = sorted(
                affiliate_commissions.values(),
                key=lambda x: (
                    x['approved_total'] > 0,  # Approved commissions first
                    x['approved_total'] + x['pending_total'] + x['paid_total'],  # Then by total earnings
                ),
                reverse=True
            )
            
            # Calculate totals - use aggregate values already computed
            total_approved = sum(a['approved_total'] for a in affiliate_commissions.values())
            total_pending = sum(a['pending_total'] for a in affiliate_commissions.values())
            total_paid = sum(a['paid_total'] for a in affiliate_commissions.values())
        
        finally:
            # Restore original timeout
            db.session.execute(text(f"SET statement_timeout = {original_timeout}"))
        
        logger.info(f"Rendering manage_commissions template with {len(sorted_affiliates)} affiliates")
        
        # Prepare data for the template - reformat for template compatibility
        grouped_commissions = {}
        for affiliate_data in sorted_affiliates:
            affiliate_id = affiliate_data['affiliate'].id
            grouped_commissions[affiliate_id] = {
                'affiliate': affiliate_data['affiliate'],
                'commissions': affiliate_data['commissions'],
                'total_amount': affiliate_data['approved_total'] + affiliate_data['pending_total']
            }
        
        # Get filter params from request (default to empty values if not present)
        status = request.args.get('status', '')
        affiliate_id = request.args.get('affiliate_id', '')
        min_amount = request.args.get('min_amount', '')
        
        return render_template('admin/manage_commissions.html',
            affiliates=sorted_affiliates,
            grouped_commissions=grouped_commissions,
            total_approved=total_approved,
            total_pending=total_pending,
            total_paid=total_paid,
            commission_status=CommissionStatus,
            status=status,
            affiliate_id=affiliate_id,
            min_amount=min_amount
        )
    except Exception as e:
        logger.error(f"Error in manage_commissions: {str(e)}", exc_info=True)
        # Simple fallback page in case of errors
        return f"""
        <html>
            <head><title>Manage Commissions Error</title></head>
            <body>
                <h1>Error Loading Commission Management</h1>
                <p>An error occurred: {str(e)}</p>
                <p>This has been logged for investigation.</p>
                <a href="/">Return to Home</a>
            </body>
        </html>
        """, 500

@admin_bp.route('/process_payouts', methods=['POST'])
@admin_required
def process_payouts():
    """Process PayPal payouts for selected affiliates"""
    try:
        # Get selected affiliates
        affiliate_ids = request.form.getlist('affiliate_id')
        
        if not affiliate_ids:
            flash('No affiliates selected for payout', 'error')
            return redirect(url_for('admin_simple.manage_commissions'))
        
        # Group commissions by affiliate
        payouts = {}
        for affiliate_id in affiliate_ids:
            # Get the affiliate (now a User in our simplified system)
            affiliate = User.query.get(affiliate_id)
            if not affiliate:
                continue
                
            # Get approved commissions for this affiliate
            commissions = Commission.query.filter_by(
                affiliate_id=affiliate_id,
                status=CommissionStatus.APPROVED.value
            ).all()
            
            if not commissions:
                continue
                
            # Calculate total amount
            amount = sum(c.commission_amount for c in commissions)
            
            # Add to payouts
            payouts[affiliate_id] = {
                'affiliate': affiliate,
                'amount': amount,
                'commissions': commissions
            }
        
        if not payouts:
            flash('No approved commissions found for selected affiliates', 'error')
            return redirect(url_for('admin_simple.manage_commissions'))
        
        # Generate a batch ID for this payout batch
        sender_batch_id = generate_sender_batch_id()
        
        # Create payout items
        payout_items = []
        for affiliate_id, payout in payouts.items():
            affiliate = payout['affiliate']
            amount = payout['amount']
            
            # Make sure we have a PayPal email
            if not affiliate.paypal_email:
                flash(f'Missing PayPal email for affiliate {affiliate.name}', 'error')
                continue
                
            # Add to payout items
            payout_items.append({
                'recipient_type': 'EMAIL',
                'amount': {
                    'value': amount,
                    'currency': 'USD'
                },
                'note': f'GloriaMundo affiliate commission payout',
                'sender_item_id': f'{sender_batch_id}_ITEM_{affiliate_id}',
                'receiver': affiliate.paypal_email
            })
        
        if not payout_items:
            flash('No valid payout items could be created', 'error')
            return redirect(url_for('admin_simple.manage_commissions'))
        
        # Process the payout with PayPal
        payout_response = process_paypal_payout(sender_batch_id, payout_items)
        payout_batch_id = payout_response['batch_header']['payout_batch_id']
        
        # Update commissions status to PROCESSING
        for affiliate_id, payout in payouts.items():
            for commission in payout['commissions']:
                commission.status = CommissionStatus.PROCESSING.value
                commission.payout_batch_id = payout_batch_id
                db.session.add(commission)
        
        db.session.commit()
        
        flash(f'Payout batch {payout_batch_id} created successfully and is now processing', 'success')
        return redirect(url_for('admin_simple.payouts'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing payouts: {str(e)}", exc_info=True)
        flash(f'Error processing payouts: {str(e)}', 'error')
        return redirect(url_for('admin_simple.manage_commissions'))

@admin_bp.route('/payouts')
@admin_required
def payouts():
    """Admin page for viewing and checking payout statuses"""
    try:
        # Get all commissions with payout_batch_id
        commissions = Commission.query.filter(
            Commission.payout_batch_id.isnot(None)
        ).order_by(
            Commission.payout_batch_id,
            Commission.affiliate_id
        ).all()
        
        # Group by batch ID
        batches = {}
        for commission in commissions:
            batch_id = commission.payout_batch_id
            if batch_id not in batches:
                batches[batch_id] = {
                    'commissions': [],
                    'total_amount': 0,
                    'status': commission.status,
                    'created_at': commission.updated_at,
                    'affiliate_count': 0,
                    'affiliate_ids': set()
                }
            
            batches[batch_id]['commissions'].append(commission)
            batches[batch_id]['total_amount'] += commission.commission_amount
            batches[batch_id]['affiliate_ids'].add(commission.affiliate_id)
        
        # Count unique affiliates
        for batch_id, batch in batches.items():
            batch['affiliate_count'] = len(batch['affiliate_ids'])
            batch['affiliate_ids'] = list(batch['affiliate_ids'])  # Convert to list for template
        
        # Sort by date (newest first)
        sorted_batches = sorted(batches.values(), key=lambda x: x['created_at'], reverse=True)
        
        return render_template('admin/payouts.html', batches=sorted_batches)
    except Exception as e:
        logger.error(f"Error in payouts: {str(e)}", exc_info=True)
        # Simple fallback page in case of errors
        return f"""
        <html>
            <head><title>Payouts Error</title></head>
            <body>
                <h1>Error Loading Payouts</h1>
                <p>An error occurred: {str(e)}</p>
                <p>This has been logged for investigation.</p>
                <a href="/">Return to Home</a>
            </body>
        </html>
        """, 500

@admin_bp.route('/check_payout_status/<batch_id>', methods=['POST'])
@admin_required
def check_payout_status_route(batch_id):
    """Check and update the status of a PayPal payout batch"""
    try:
        # Get the batch from PayPal
        payout_status = check_payout_status(batch_id)
        batch_status = payout_status['batch_header']['batch_status']
        
        # Get all commissions for this batch
        commissions = Commission.query.filter_by(payout_batch_id=batch_id).all()
        
        # Update status
        if batch_status == 'SUCCESS':
            # Mark all as paid
            for commission in commissions:
                commission.status = CommissionStatus.PAID.value
                db.session.add(commission)
            
            db.session.commit()
            flash(f'Payout batch {batch_id} completed successfully. All commissions marked as paid.', 'success')
        else:
            # Just show the status
            flash(f'Payout batch {batch_id} status: {batch_status}', 'info')
        
        return redirect(url_for('admin_simple.payouts'))
    except Exception as e:
        logger.error(f"Error checking payout status: {str(e)}", exc_info=True)
        flash(f'Error checking payout status: {str(e)}', 'error')
        return redirect(url_for('admin_simple.payouts'))

@admin_bp.route('/toggle_paypal_mode', methods=['POST'])
@admin_required
def toggle_paypal_mode():
    """Toggle between PayPal sandbox and live modes"""
    current_mode = os.environ.get('PAYPAL_MODE', 'sandbox')
    new_mode = 'live' if current_mode == 'sandbox' else 'sandbox'
    
    # Set environment variable
    os.environ['PAYPAL_MODE'] = new_mode
    
    # In a production app, we would update a configuration file or database setting
    # But for simplicity, we're just toggling the environment variable in memory
    
    flash(f'PayPal mode changed from {current_mode} to {new_mode}.', 'success')
    return redirect(url_for('admin_simple.index'))

@admin_bp.route('/approve_commission/<int:commission_id>', methods=['POST'])
@admin_required
def approve_commission(commission_id):
    """Approve a commission for payout"""
    try:
        commission = Commission.query.get(commission_id)
        if not commission:
            flash('Commission not found', 'error')
            return redirect(url_for('admin_simple.manage_commissions'))
            
        commission.status = CommissionStatus.APPROVED.value
        db.session.commit()
        
        flash(f'Commission #{commission_id} approved for payout', 'success')
        return redirect(url_for('admin_simple.manage_commissions'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error approving commission: {str(e)}", exc_info=True)
        flash(f'Error approving commission: {str(e)}', 'error')
        return redirect(url_for('admin_simple.manage_commissions'))

@admin_bp.route('/reject_commission/<int:commission_id>', methods=['POST'])
@admin_required
def reject_commission(commission_id):
    """Reject a commission (e.g., if the associated purchase was refunded)"""
    try:
        commission = Commission.query.get(commission_id)
        if not commission:
            flash('Commission not found', 'error')
            return redirect(url_for('admin_simple.manage_commissions'))
            
        commission.status = CommissionStatus.REJECTED.value
        db.session.commit()
        
        flash(f'Commission #{commission_id} rejected', 'success')
        return redirect(url_for('admin_simple.manage_commissions'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error rejecting commission: {str(e)}", exc_info=True)
        flash(f'Error rejecting commission: {str(e)}', 'error')
        return redirect(url_for('admin_simple.manage_commissions'))

# --- ELO Score Management Routes ---

@admin_bp.route('/elo-management')
@admin_required
def elo_management():
    """Admin page for managing ELO scores"""
    try:
        # Get all models with pagination
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str)
        per_page = 50  # Show 50 models per page
        
        # Build query
        query = OpenRouterModel.query.filter(OpenRouterModel.model_is_active == True)
        
        # Add search filter if provided
        if search:
            query = query.filter(OpenRouterModel.model_id.ilike(f'%{search}%'))
            # When searching, show more results per page to be more useful
            per_page = 200
        
        # Order by model_id for consistent pagination
        query = query.order_by(OpenRouterModel.model_id)
        
        # Paginate
        models = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Get summary stats
        total_models = OpenRouterModel.query.filter(OpenRouterModel.model_is_active == True).count()
        models_with_elo = OpenRouterModel.query.filter(
            OpenRouterModel.model_is_active == True,
            OpenRouterModel.elo_score.isnot(None)
        ).count()
        
        return render_template('admin/elo_management.html',
                             models=models,
                             search=search,
                             total_models=total_models,
                             models_with_elo=models_with_elo)
                             
    except Exception as e:
        logger.error(f"Error in ELO management: {str(e)}", exc_info=True)
        flash(f'Error loading ELO management: {str(e)}', 'error')
        return redirect(url_for('admin_simple.index'))

@admin_bp.route('/update-elo-score', methods=['POST'])
@admin_required
def update_elo_score():
    """Update ELO score for a specific model"""
    try:
        model_id = request.form.get('model_id')
        elo_score_str = request.form.get('elo_score', '').strip()
        
        if not model_id:
            flash('Model ID is required', 'error')
            return redirect(url_for('admin_simple.elo_management'))
        
        # Find the model
        model = OpenRouterModel.query.filter_by(model_id=model_id).first()
        if not model:
            flash('Model not found', 'error')
            return redirect(url_for('admin_simple.elo_management'))
        
        # Parse ELO score
        elo_score = None
        if elo_score_str:
            try:
                elo_score = int(elo_score_str)
            except ValueError:
                flash('ELO score must be a whole number', 'error')
                return redirect(url_for('admin_simple.elo_management'))
        
        # Update the model
        old_score = model.elo_score
        model.elo_score = elo_score
        db.session.commit()
        
        # Log the change
        logger.info(f"ELO score updated for {model_id}: {old_score} -> {elo_score} by {current_user.email}")
        
        # Check if this is an AJAX request
        from flask import jsonify
        if request.is_json or 'application/json' in request.headers.get('Accept', ''):
            # Return JSON response for AJAX
            return jsonify({
                'success': True,
                'message': f'ELO score {"cleared" if elo_score is None else "updated"} for {model_id}',
                'elo_score': elo_score
            })
        else:
            # Regular form submission - redirect with flash message
            if elo_score is None:
                flash(f'ELO score cleared for {model_id}', 'success')
            else:
                flash(f'ELO score updated for {model_id}: {elo_score}', 'success')
                
            return redirect(url_for('admin_simple.elo_management', search=request.form.get('search', '')))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating ELO score: {str(e)}", exc_info=True)
        flash(f'Error updating ELO score: {str(e)}', 'error')
        return redirect(url_for('admin_simple.elo_management'))

@admin_bp.route('/reset-all-elo-scores', methods=['POST'])
@admin_required
def reset_all_elo_scores():
    """Reset all ELO scores to NULL"""
    try:
        # Count how many models have ELO scores currently
        models_with_elo = OpenRouterModel.query.filter(
            OpenRouterModel.elo_score.isnot(None)
        ).count()
        
        # Reset all ELO scores to NULL
        OpenRouterModel.query.update({OpenRouterModel.elo_score: None})
        db.session.commit()
        
        # Log the action
        logger.info(f"All ELO scores reset to NULL by {current_user.email}. {models_with_elo} models affected.")
        
        flash(f'Reset {models_with_elo} ELO scores to blank', 'success')
        return redirect(url_for('admin_simple.elo_management'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resetting ELO scores: {str(e)}", exc_info=True)
        flash(f'Error resetting ELO scores: {str(e)}', 'error')
        return redirect(url_for('admin_simple.elo_management'))

def init_admin(app):
    """Register the admin blueprint with the app"""
    app.register_blueprint(admin_bp)
    return admin_bp
