"""
Billing Module for GloriaMundo Chatbot

This module handles billing routes, account management, and credit purchases.
It provides endpoints for:
1. Account management page
2. Credit purchase through Stripe
3. Credit usage tracking
4. Affiliate commission processing
"""

import os
import logging
import math
from datetime import datetime, timedelta
from urllib.parse import urlparse
import io
import uuid
import stripe

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify, g, send_file, Response
from flask_login import current_user, login_required
from sqlalchemy import desc, func, and_
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch, cm

# Import database instance and models
from database import db
from models import User, Transaction, Usage, Package, PaymentStatus
from models import CustomerReferral, Commission, CommissionStatus
# AffiliateStatus is no longer needed since affiliate functionality is handled by User model
from stripe_config import initialize_stripe, create_checkout_session, verify_webhook_signature, retrieve_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
billing_bp = Blueprint('billing', __name__)

# Initialize Stripe
initialize_stripe()

@billing_bp.route('/account', methods=['GET'])
@login_required
def account_management():
    """
    Account management page showing credit balance, usage history, and purchase options.
    """
    try:
        logger.info(f"Loading account management page for user: {current_user.id} - {current_user.email}")
        
        # Get packages
        packages = Package.query.filter_by(is_active=True).all()
        logger.debug(f"Found {len(packages)} active packages")
        
        # Get recent transactions, filter out test mode transactions (those with stripe_payment_intent starting with 'pi_test_')
        transaction_query = Transaction.query.filter_by(user_id=current_user.id)
        
        # Filter out test transactions (those with payment_intent starting with 'pi_test_')
        live_transactions = []
        for transaction in transaction_query.order_by(desc(Transaction.created_at)).all():
            # If it's a Stripe transaction, check if it's a test one
            if transaction.payment_method == 'stripe' and transaction.stripe_payment_intent:
                if not transaction.stripe_payment_intent.startswith('pi_test_'):
                    live_transactions.append(transaction)
            else:
                # Non-Stripe transactions or those without a payment intent are included
                live_transactions.append(transaction)
        
        # Limit to 5 transactions for display
        recent_transactions = live_transactions[:5]
        logger.debug(f"Found {len(recent_transactions)} live-mode recent transactions")
        
        # Get usage from last 24 hours by default
        last_24h = datetime.utcnow() - timedelta(days=1)
        recent_usage = Usage.query.filter_by(user_id=current_user.id) \
            .filter(Usage.created_at >= last_24h) \
            .order_by(desc(Usage.created_at)).all()
        logger.debug(f"Found {len(recent_usage)} usage records in the last 24 hours")
        
        # In the simplified affiliate system, every user is automatically an affiliate
        # Just ensure they have a referral code
        if not current_user.referral_code:
            logger.info(f"No referral code found for user: {current_user.email}, generating one")
            try:
                # Generate a unique referral code
                current_user.generate_referral_code()
                db.session.commit()
                logger.info(f"Successfully generated referral code {current_user.referral_code} for user: {current_user.email}")
            except Exception as e:
                logger.error(f"Error generating referral code: {e}")
                
        # Log the user's affiliate status
        logger.info(f"User affiliate status: id={current_user.id}, referral_code={current_user.referral_code}")
            
        # Get commission statistics for the user
        commission_stats = {}
        commissions = []
        referrals = []
        sub_referrals = []
        
        # All users are considered active affiliates in the simplified system
        # Get total earned commissions (affiliate_id now refers to user_id in our simplified system)
        earned_commissions = db.session.query(func.sum(Commission.commission_amount)).filter(
            Commission.affiliate_id == current_user.id,
            Commission.status.in_([CommissionStatus.APPROVED.value, CommissionStatus.PAID.value])
        ).scalar() or 0
            
        # Get pending commissions (affiliate_id now refers to user_id in our simplified system)
        pending_commissions = db.session.query(func.sum(Commission.commission_amount)).filter(
            Commission.affiliate_id == current_user.id,
            Commission.status == CommissionStatus.HELD.value
        ).scalar() or 0
        
        # Get referral count (affiliate_id now refers to user_id in our simplified system)
        referral_count = CustomerReferral.query.filter_by(affiliate_id=current_user.id).count()
        
        # Calculate conversion rate - set as N/A since click tracking isn't implemented
        commission_stats = {
            'total_earned': f'{earned_commissions:.2f}',
            'pending': f'{pending_commissions:.2f}',
            'referrals': referral_count,
            'conversion_rate': 'N/A'  # Use N/A until click tracking is implemented
        }
        
        # Get recent commissions for dashboard view (affiliate_id now refers to user_id in our simplified system)
        commissions = Commission.query.filter_by(affiliate_id=current_user.id) \
            .order_by(desc(Commission.created_at)).limit(10).all()
        
        # Get referred users (direct referrals)
        referral_query = db.session.query(
            User, 
            func.sum(Transaction.amount_usd).label('total_purchases')
        ).join(
            CustomerReferral, CustomerReferral.customer_user_id == User.id
        ).outerjoin(
            Transaction, Transaction.user_id == User.id
        ).filter(
            CustomerReferral.affiliate_id == current_user.id
        ).group_by(
            User.id
        ).order_by(
            desc(User.created_at)
        ).limit(10)
        
        referrals = []
        for user, total_purchases in referral_query:
            referrals.append({
                'id': user.id,
                'username': user.username,
                'created_at': user.created_at,
                'total_purchases': f'{total_purchases or 0:.2f}'
            })
            
        # Get sub-affiliates (tier 2) - users who were referred by users that current_user referred
        # Using aliases to avoid duplicate table name issues
        from sqlalchemy.orm import aliased
        
        # Create aliases for the User table
        ReferredUser = aliased(User)
        ReferringUser = aliased(User)
        
        sub_affiliate_query = db.session.query(
            ReferredUser,
            func.sum(Transaction.amount_usd).label('total_purchases')
        ).join(
            CustomerReferral, CustomerReferral.customer_user_id == ReferredUser.id
        ).join(
            ReferringUser, ReferringUser.id == CustomerReferral.affiliate_id, isouter=True
        ).outerjoin(
            Transaction, Transaction.user_id == ReferredUser.id
        ).filter(
            ReferredUser.referred_by_user_id.in_(
                db.session.query(ReferringUser.id).filter(ReferringUser.referred_by_user_id == current_user.id)
            )
        ).group_by(
            ReferredUser.id
        ).order_by(
            desc(ReferredUser.created_at)
        ).limit(5)
        
        sub_referrals = []
        for sub_user, total_purchases in sub_affiliate_query:
            sub_referrals.append({
                'id': sub_user.id,
                'username': sub_user.username,
                'created_at': sub_user.created_at,
                'total_purchases': f'{total_purchases or 0:.2f}'
            })
        
        # Add detailed logging of values passed to template
        # In our simplified system, all users are considered active affiliates
        logger.info(f"User affiliate info: id={current_user.id}, email={current_user.email}, referral_code={current_user.referral_code}")
        logger.info(f"Commission stats: {commission_stats}")
        logger.info(f"Commissions count: {len(commissions)}")
        logger.info(f"Referrals count: {len(referrals)}")
        logger.info(f"Sub-referrals count: {len(sub_referrals)}")
        
        logger.info("Rendering account.html template")
        return render_template(
            'account.html',
            user=current_user,
            packages=packages,
            recent_transactions=recent_transactions,
            recent_usage=recent_usage,
            # In the simplified system, the user is the affiliate
            affiliate=current_user,  # For backward compatibility with templates
            commission_stats=commission_stats,
            commissions=commissions,
            referrals=referrals,
            sub_referrals=sub_referrals,
            stats=commission_stats  # Alias to match dashboard template
        )
    
    except Exception as e:
        logger.error(f"Error in account_management: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('index'))

@billing_bp.route('/purchase/<int:package_id>', methods=['POST'])
@login_required
def purchase_package(package_id):
    """
    Initiate a credit package purchase using Stripe.
    
    Args:
        package_id: ID of the package to purchase
    """
    try:
        # Get package
        package = Package.query.get(package_id)
        if not package:
            flash("Invalid package selected", "error")
            return redirect(url_for('billing.account_management'))
        
        # Check if user has completed transactions
        has_previous_purchases = db.session.query(Transaction).filter(
            Transaction.user_id == current_user.id,
            Transaction.status == PaymentStatus.COMPLETED.value
        ).count() > 0
        
        # Check if this is the Starter Pack ($5) and if the user has previous transactions
        is_starter_package = package.id == 1  # ID 1 is the $5 Starter Package
        if is_starter_package and has_previous_purchases:
            flash("The Starter Credit Pack is only available for first-time purchases.", "error")
            return redirect(url_for('billing.account_management'))
        
        # Create return URLs
        base_url = request.host_url.rstrip('/')
        success_url = f"{base_url}{url_for('billing.payment_success')}?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}{url_for('billing.cancel_purchase')}"
        
        # Check if this is the user's first purchase
        is_first_purchase = not has_previous_purchases
        
        # Create Stripe Checkout Session
        checkout_result = create_checkout_session(
            price_id=package.stripe_price_id,
            user_id=current_user.id,
            success_url=success_url,
            cancel_url=cancel_url,
            is_first_purchase=is_first_purchase
        )
        
        if checkout_result["success"]:
            # Create transaction record
            transaction = Transaction(
                user_id=current_user.id,
                package_id=package.id,
                amount_usd=package.amount_usd,
                credits=package.credits,
                payment_method="stripe",
                payment_id=checkout_result["session_id"],
                status=PaymentStatus.PENDING.value
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Redirect to Stripe Checkout
            return redirect(checkout_result["checkout_url"])
        else:
            flash(f"Error creating Stripe Checkout: {checkout_result.get('error', 'Unknown error')}", "error")
            return redirect(url_for('billing.account_management'))
    
    except Exception as e:
        logger.error(f"Error in purchase_package: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('billing.account_management'))

# Custom amount purchase has been removed in the Stripe integration

@billing_bp.route('/cancel', methods=['GET'])
@login_required
def cancel_purchase():
    """
    Handle cancelled payments.
    """
    try:
        flash("Payment was cancelled", "info")
        return redirect(url_for('billing.account_management'))
    
    except Exception as e:
        logger.error(f"Error in cancel_purchase: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('billing.account_management'))

@billing_bp.route('/payment-success', methods=['GET'])
@login_required
def payment_success():
    """
    Handle successful Stripe payments.
    This is just a redirect page after a successful checkout.
    The actual payment processing happens in the webhook.
    """
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            flash("Invalid session ID", "error")
            return redirect(url_for('billing.account_management'))
        
        # Display success message
        flash("Payment successful! Your credits will be added shortly.", "success")
        return redirect(url_for('billing.account_management'))
    
    except Exception as e:
        logger.error(f"Error in payment_success: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('billing.account_management'))

@billing_bp.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhook events.
    This endpoint receives webhook events from Stripe and processes completed payments.
    """
    try:
        # Get the webhook payload and signature header
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        if not webhook_secret:
            logger.error("Stripe webhook secret missing")
            return jsonify({'error': 'Webhook secret missing'}), 500
        
        # Verify the webhook signature
        verification_result = verify_webhook_signature(payload, sig_header, webhook_secret)
        
        if not verification_result["success"]:
            logger.error(f"Webhook signature verification failed: {verification_result.get('error')}")
            return jsonify({'error': 'Signature verification failed'}), 400
        
        # Get the event
        event = verification_result["event"]
        
        # Handle the checkout.session.completed event
        if event.type == 'checkout.session.completed':
            session = event.data.object  # checkout session object
            
            # Get customer details
            customer_id = session.client_reference_id
            if not customer_id:
                logger.error("No client_reference_id in session")
                return jsonify({'error': 'No client reference ID'}), 400
            
            # Convert customer_id to integer
            try:
                user_id = int(customer_id)
            except ValueError:
                logger.error(f"Invalid client_reference_id: {customer_id}")
                return jsonify({'error': 'Invalid client reference ID'}), 400
            
            # Find the pending transaction
            transaction = Transaction.query.filter_by(
                user_id=user_id,
                payment_id=session.id,
                status=PaymentStatus.PENDING.value
            ).first()
            
            if not transaction:
                logger.error(f"No pending transaction found for session {session.id}")
                return jsonify({'error': 'Transaction not found'}), 404
            
            # Process the payment
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return jsonify({'error': 'User not found'}), 404
            
            # Update transaction status and payment intent ID
            transaction.status = PaymentStatus.COMPLETED.value
            transaction.stripe_payment_intent = session.payment_intent
            transaction.updated_at = datetime.utcnow()
            
            # Add credits to user account
            user.add_credits(transaction.credits)
            
            # Process affiliate commissions if applicable
            process_affiliate_commission(user.id, transaction)
            
            # Save changes
            db.session.commit()
            
            logger.info(f"Payment for {transaction.credits} credits processed successfully for user {user.id}")
            
        # Return a success response
        return jsonify({'status': 'success'}), 200
    
    except Exception as e:
        logger.error(f"Error in stripe_webhook: {e}")
        return jsonify({'error': str(e)}), 500

@billing_bp.route('/usage', methods=['GET'])
@login_required
def usage_history():
    """
    View detailed usage history.
    """
    try:
        # Get date range param or default to 'all'
        date_range = request.args.get('range', 'all')
        
        # Create base query
        query = Usage.query.filter_by(user_id=current_user.id)
        
        # Apply date filtering based on selected range
        now = datetime.utcnow()
        if date_range == '1':  # Last 24 hours
            start_date = now - timedelta(days=1)
            query = query.filter(Usage.created_at >= start_date)
        elif date_range == '7':  # Last 7 days
            start_date = now - timedelta(days=7)
            query = query.filter(Usage.created_at >= start_date)
        elif date_range == '30':  # Last 30 days
            start_date = now - timedelta(days=30)
            query = query.filter(Usage.created_at >= start_date)
        elif date_range == 'month':  # This month
            start_date = datetime(now.year, now.month, 1)
            query = query.filter(Usage.created_at >= start_date)
        
        # Get all filtered usage records
        usage_list = query.order_by(desc(Usage.created_at)).all()
        
        return render_template(
            'usage_history.html',
            usage_list=usage_list
        )
    
    except Exception as e:
        logger.error(f"Error in usage_history: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('billing.account_management'))

@billing_bp.route('/get-usage-by-range', methods=['GET'])
@login_required
def get_usage_by_range():
    """
    API endpoint to get usage data filtered by date range.
    """
    try:
        # Get date range param, default to '1' (24 hours)
        date_range = request.args.get('range', '1')
        
        # Create base query
        query = Usage.query.filter_by(user_id=current_user.id)
        
        # Apply date filtering based on selected range
        now = datetime.utcnow()
        if date_range == '1':  # Last 24 hours
            start_date = now - timedelta(days=1)
            query = query.filter(Usage.created_at >= start_date)
        elif date_range == '7':  # Last 7 days
            start_date = now - timedelta(days=7)
            query = query.filter(Usage.created_at >= start_date)
        elif date_range == '30':  # Last 30 days
            start_date = now - timedelta(days=30)
            query = query.filter(Usage.created_at >= start_date)
        elif date_range == 'month':  # This month
            start_date = datetime(now.year, now.month, 1)
            query = query.filter(Usage.created_at >= start_date)
        
        # Get usage data with applied filters
        usage_data = query.order_by(desc(Usage.created_at)).all()
        
        # Format data for response
        results = []
        for usage in usage_data:
            results.append({
                'id': usage.id,
                'created_at': usage.created_at.strftime('%Y-%m-%d %H:%M'),
                'credits_used': usage.credits_used,
                'model_id': usage.model_id,
                'usage_type': usage.usage_type,
                'prompt_tokens': usage.prompt_tokens,
                'completion_tokens': usage.completion_tokens
            })
        
        # Calculate summary stats
        total_credits = sum(usage.credits_used for usage in usage_data)
        total_requests = len(usage_data)
        
        return jsonify({
            'success': True,
            'usage': results,
            'total_credits': total_credits,
            'total_requests': total_requests,
            'date_range': date_range
        })
    
    except Exception as e:
        logger.error(f"Error in get_usage_by_range: {e}")
        return jsonify({
            'success': False,
            'message': f"Error retrieving usage data: {str(e)}"
        }), 500

@billing_bp.route('/update-memory-preference', methods=['POST'])
@login_required
def update_memory_preference():
    """
    Update the user's memory preference setting.
    """
    try:
        # Get the preference value from the request
        enable_memory = request.json.get('enable_memory', True)
        
        # Update the user's preference
        current_user.enable_memory = enable_memory
        db.session.commit()
        
        logger.info(f"Updated memory preference for user {current_user.id} to {enable_memory}")
        
        return jsonify({
            "success": True,
            "message": "Memory preference updated successfully",
            "enable_memory": enable_memory
        })
    
    except Exception as e:
        logger.error(f"Error updating memory preference: {e}")
        return jsonify({
            "success": False,
            "message": f"Error updating preference: {str(e)}"
        }), 500


@billing_bp.route('/update-fallback-preference', methods=['POST'])
@login_required
def update_fallback_preference():
    """
    Update the user's model fallback preference setting.
    """
    try:
        # Get the preference value from the request
        enable_model_fallback = request.json.get('enable_model_fallback', True)
        
        # Update the user's preference
        current_user.enable_model_fallback = enable_model_fallback
        db.session.commit()
        
        logger.info(f"Updated model fallback preference for user {current_user.id} to {enable_model_fallback}")
        
        return jsonify({
            "success": True,
            "message": "Model fallback preference updated successfully",
            "enable_model_fallback": enable_model_fallback
        })
    
    except Exception as e:
        logger.error(f"Error updating model fallback preference: {e}")
        return jsonify({
            "success": False,
            "message": f"Error updating preference: {str(e)}"
        }), 500

@billing_bp.route('/transactions', methods=['GET'])
@login_required
def transaction_history():
    """
    View transaction history.
    """
    try:
        # Get all transactions
        transactions = Transaction.query.filter_by(user_id=current_user.id) \
            .order_by(desc(Transaction.created_at)).all()
        
        return render_template(
            'transaction_history.html',
            transactions=transactions
        )
    
    except Exception as e:
        logger.error(f"Error in transaction_history: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('billing.account_management'))

@billing_bp.route('/export-transactions', methods=['GET'])
@login_required
def export_transactions_csv():
    """
    Export transaction history as a CSV file.
    """
    try:
        # Get all transactions for the current user
        transactions = Transaction.query.filter_by(user_id=current_user.id) \
            .order_by(desc(Transaction.created_at)).all()
        
        if not transactions:
            flash("No transactions to export", "info")
            return redirect(url_for('billing.account_management'))
        
        # Create CSV content
        csv_content = io.StringIO()
        csv_content.write("Transaction ID,Date,Amount,Credits,Payment Method,Status,Receipt Number\n")
        
        for transaction in transactions:
            # Format date
            date_str = transaction.created_at.strftime('%Y-%m-%d')
            
            # Generate receipt number (only for completed transactions)
            receipt_number = ""
            if transaction.status == PaymentStatus.COMPLETED.value:
                receipt_number = f"R-{transaction.id}-{transaction.stripe_payment_intent[-6:] if transaction.stripe_payment_intent else 'XXXX'}"
            
            # Format row
            row = f"{transaction.id},{date_str},${transaction.amount_usd:.2f},{transaction.credits},{transaction.payment_method},{transaction.status},{receipt_number}\n"
            csv_content.write(row)
        
        # Prepare response
        csv_content.seek(0)
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        filename = f"transactions_{timestamp}.csv"
        
        return Response(
            csv_content.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    
    except Exception as e:
        logger.error(f"Error exporting transactions: {e}")
        flash(f"An error occurred while exporting transactions: {str(e)}", "error")
        return redirect(url_for('billing.account_management'))

@billing_bp.route('/export-usage', methods=['GET'])
@login_required
def export_usage_csv():
    """
    Export usage analytics as a CSV file.
    """
    try:
        # Get date range param or default to 'all'
        date_range = request.args.get('range', 'all')
        
        # Create base query
        query = Usage.query.filter_by(user_id=current_user.id)
        
        # Apply date filtering based on selected range
        now = datetime.utcnow()
        if date_range == '1':  # Last 24 hours
            start_date = now - timedelta(days=1)
            query = query.filter(Usage.created_at >= start_date)
        elif date_range == '7':  # Last 7 days
            start_date = now - timedelta(days=7)
            query = query.filter(Usage.created_at >= start_date)
        elif date_range == '30':  # Last 30 days
            start_date = now - timedelta(days=30)
            query = query.filter(Usage.created_at >= start_date)
        elif date_range == 'month':  # This month
            start_date = datetime(now.year, now.month, 1)
            query = query.filter(Usage.created_at >= start_date)
        
        # Get all filtered usage records
        usage_list = query.order_by(desc(Usage.created_at)).all()
        
        if not usage_list:
            flash("No usage data to export for the selected date range", "info")
            return redirect(url_for('billing.account_management'))
        
        # Create CSV content
        csv_content = io.StringIO()
        csv_content.write("Date,Time,Type,Model,Input Tokens,Input Cost,Output Tokens,Output Cost,Total Cost\n")
        
        for usage in usage_list:
            # Format date and time
            date_str = usage.created_at.strftime('%Y-%m-%d')
            time_str = usage.created_at.strftime('%H:%M:%S')
            
            # Get usage data
            usage_type = usage.usage_type or 'Unknown'
            model_name = usage.model_id.split('/')[-1] if usage.model_id else 'Unknown'
            input_tokens = usage.prompt_tokens or 0
            output_tokens = usage.completion_tokens or 0
            credits_used = usage.credits_used or 0
            # Convert credits to USD (100,000 credits = $1)
            total_cost = credits_used / 100000
            # Estimate input/output costs (this is an approximation)
            input_cost = total_cost * 0.6  # Roughly 60% for input
            output_cost = total_cost * 0.4  # Roughly 40% for output
            
            # Format row
            row = f'"{date_str}","{time_str}","{usage_type}","{model_name}",{input_tokens},{input_cost:.6f},{output_tokens},{output_cost:.6f},{total_cost:.6f}\n'
            csv_content.write(row)
        
        # Prepare response
        csv_content.seek(0)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        range_suffix = f"_{date_range}days" if date_range.isdigit() else f"_{date_range}"
        filename = f"usage_analytics{range_suffix}_{timestamp}.csv"
        
        return Response(
            csv_content.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    
    except Exception as e:
        logger.error(f"Error exporting usage data: {e}")
        flash(f"An error occurred while exporting usage data: {str(e)}", "error")
        return redirect(url_for('billing.account_management'))

@billing_bp.route('/receipt/<int:transaction_id>', methods=['GET'])
@login_required
def generate_receipt(transaction_id):
    """
    Generate and download a PDF receipt for a completed transaction.
    
    Args:
        transaction_id (int): ID of the transaction to generate receipt for
    """
    try:
        # Get transaction details
        transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first()
        
        if not transaction:
            flash("Transaction not found or does not belong to you", "error")
            return redirect(url_for('billing.account_management'))
        
        # Check if transaction is completed
        if transaction.status != PaymentStatus.COMPLETED.value:
            flash("Receipt is only available for completed transactions", "warning")
            return redirect(url_for('billing.account_management'))
        
        # Get user and package details
        user = User.query.get(transaction.user_id)
        package = None
        if transaction.package_id:
            package = Package.query.get(transaction.package_id)
        
        # Try to get additional details from Stripe
        tax_details = None
        billing_address = None
        stripe_payment_method = None
        payment_date = transaction.updated_at or transaction.created_at
        
        if transaction.payment_method == "stripe" and transaction.payment_id:
            # Retrieve session from Stripe
            session_result = retrieve_session(transaction.payment_id)
            
            if session_result["success"]:
                session = session_result["session"]
                
                # Try to get tax details
                if hasattr(session, 'total_details') and session.total_details:
                    tax_details = {
                        'tax_amount': session.total_details.amount_tax / 100 if hasattr(session.total_details, 'amount_tax') else 0,
                        'tax_rate': None  # Stripe doesn't directly provide the tax rate percentage
                    }
                
                # Try to get customer details
                if hasattr(session, 'customer_details') and session.customer_details:
                    if hasattr(session.customer_details, 'address') and session.customer_details.address:
                        address = session.customer_details.address
                        billing_address = {
                            'line1': getattr(address, 'line1', ''),
                            'line2': getattr(address, 'line2', ''),
                            'city': getattr(address, 'city', ''),
                            'state': getattr(address, 'state', ''),
                            'postal_code': getattr(address, 'postal_code', ''),
                            'country': getattr(address, 'country', '')
                        }
                
                # Get payment method details if available
                if transaction.stripe_payment_intent:
                    try:
                        payment_intent = stripe.PaymentIntent.retrieve(transaction.stripe_payment_intent)
                        # Handle different ways to access payment_method
                        payment_method_id = None
                        
                        # Try dictionary-style access first
                        if isinstance(payment_intent, dict) and 'payment_method' in payment_intent:
                            payment_method_id = payment_intent['payment_method']
                        # Then try attribute-style access
                        elif hasattr(payment_intent, 'payment_method'):
                            payment_method_id = payment_intent.payment_method
                            # If it's an expandable field, it might be an object with an 'id' attribute
                            if not isinstance(payment_method_id, str) and hasattr(payment_method_id, 'id'):
                                payment_method_id = payment_method_id.id
                        
                        # If we have a string payment method ID, retrieve it
                        if isinstance(payment_method_id, str):
                            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
                            if payment_method and hasattr(payment_method, 'card') and payment_method.card:
                                stripe_payment_method = {
                                    'brand': payment_method.card.brand.capitalize() if hasattr(payment_method.card, 'brand') else 'Card',
                                    'last4': payment_method.card.last4 if hasattr(payment_method.card, 'last4') else '****'
                                }
                    except Exception as e:
                        logger.warning(f"Could not retrieve payment method details: {e}")
        
        # Generate receipt PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Set up the PDF with receipt information
        # Company Logo and Header Information
        p.setFont("Helvetica-Bold", 18)
        p.drawString(50, height - 50, "Sentigral Limited")
        
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 70, "UK Company Number 11278228")
        p.drawString(50, height - 85, "VAT Number GB354005139")
        p.drawString(50, height - 100, "21 Deacon Gardens, Seaton Carew")
        p.drawString(50, height - 115, "Hartlepool, England, TS25 1UU")
        
        # Receipt Title and Number
        p.setFont("Helvetica-Bold", 14)
        receipt_number = f"R-{transaction.id}-{uuid.uuid4().hex[:6].upper()}"
        p.drawString(width - 200, height - 50, "RECEIPT")
        p.setFont("Helvetica", 12)
        p.drawString(width - 200, height - 70, f"Receipt #: {receipt_number}")
        p.drawString(width - 200, height - 85, f"Date: {payment_date.strftime('%Y-%m-%d')}")
        
        # Billing Information
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, height - 150, "Billed To:")
        p.setFont("Helvetica", 11)
        
        start_y = height - 170
        # Safely access user attributes
        username = user.username if user and hasattr(user, 'username') else "Customer"
        email = user.email if user and hasattr(user, 'email') else ""
        
        p.drawString(50, start_y, f"{username}")
        if email:
            p.drawString(50, start_y - 15, f"Email: {email}")
        
        if billing_address:
            line_y = start_y - 35
            if billing_address['line1']:
                p.drawString(50, line_y, billing_address['line1'])
                line_y -= 15
            if billing_address['line2']:
                p.drawString(50, line_y, billing_address['line2'])
                line_y -= 15
            
            address_line = []
            if billing_address['city']:
                address_line.append(billing_address['city'])
            if billing_address['state']:
                address_line.append(billing_address['state'])
            if address_line:
                p.drawString(50, line_y, ", ".join(address_line))
                line_y -= 15
                
            if billing_address['postal_code']:
                p.drawString(50, line_y, billing_address['postal_code'])
                line_y -= 15
            if billing_address['country']:
                p.drawString(50, line_y, billing_address['country'])
                line_y -= 15
        
        # Payment Information
        p.setFont("Helvetica-Bold", 12)
        p.drawString(width - 200, height - 150, "Payment Method:")
        p.setFont("Helvetica", 11)
        
        payment_info = "Stripe"
        if stripe_payment_method:
            payment_info = f"{stripe_payment_method['brand']} ending in {stripe_payment_method['last4']}"
        
        p.drawString(width - 200, height - 170, payment_info)
        p.drawString(width - 200, height - 185, f"Transaction ID: {transaction.id}")
        
        # Line
        p.line(50, height - 225, width - 50, height - 225)
        
        # Description and Amounts
        description_y = height - 250
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, description_y, "Description")
        p.drawString(width - 200, description_y, "Amount")
        
        p.setFont("Helvetica", 11)
        description = f"Credit Package: {package.name if package else 'Credits'}"
        p.drawString(50, description_y - 25, description)
        p.drawString(width - 200, description_y - 25, f"${transaction.amount_usd:.2f}")
        
        # Tax information if available
        subtotal = transaction.amount_usd
        tax_amount = 0
        
        if tax_details and tax_details['tax_amount'] > 0:
            tax_amount = tax_details['tax_amount']
            p.drawString(50, description_y - 50, "Tax")
            p.drawString(width - 200, description_y - 50, f"${tax_amount:.2f}")
        
        # Total
        total = subtotal + tax_amount
        p.setFont("Helvetica-Bold", 12)
        p.line(width - 200, description_y - 65, width - 50, description_y - 65)
        p.drawString(50, description_y - 80, "Total")
        p.drawString(width - 200, description_y - 80, f"${total:.2f}")
        
        # Footer
        p.setFont("Helvetica", 10)
        footer_text = "Thank you for your business!"
        p.drawString((width - p.stringWidth(footer_text, "Helvetica", 10)) / 2, 50, footer_text)
        
        # Save PDF
        p.showPage()
        p.save()
        buffer.seek(0)
        
        # Create filename for the receipt
        filename = f"receipt_{receipt_number}.pdf"
        
        # Return the PDF as a download
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    
    except Exception as e:
        logger.error(f"Error generating receipt: {e}")
        flash(f"An error occurred while generating the receipt: {str(e)}", "error")
        return redirect(url_for('billing.account_management'))

def calculate_openrouter_credits(prompt_tokens, completion_tokens, model_id):
    """
    Calculate credits used for an OpenRouter request using dynamic pricing.
    
    Args:
        prompt_tokens (int): Number of prompt tokens
        completion_tokens (int): Number of completion tokens
        model_id (str): The ID of the model to use
        
    Returns:
        int: Credits used
    """
    # Import here to avoid circular imports
    from price_updater import get_model_cost
    
    # Get model costs from the cached pricing data
    model_costs = get_model_cost(model_id)
    prompt_cost_per_million = model_costs['prompt_cost_per_million']
    completion_cost_per_million = model_costs['completion_cost_per_million']
    
    # Calculate token costs
    prompt_cost = (prompt_tokens / 1000000) * prompt_cost_per_million
    completion_cost = (completion_tokens / 1000000) * completion_cost_per_million
    
    # Calculate total cost
    total_cost_usd = prompt_cost + completion_cost
    
    # Apply markup (2x)
    user_cost_usd = total_cost_usd * 2
    
    # Convert to credits (1 credit = $0.00001)
    # $1 = 100,000 credits
    credits = int(user_cost_usd * 100000)
    
    return credits

def calculate_embedding_credits(token_count):
    """
    Calculate credits used for embedding generation.
    
    Args:
        token_count (int): Number of tokens
        
    Returns:
        int: Credits used
    """
    # $1 per million tokens for text-embedding-3-large
    token_cost = 1.0 / 1000000  # Cost per token
    
    # Calculate total cost
    total_cost = token_count * token_cost
    
    # Convert to credits (1 credit = $0.00001)
    # $1 = 100,000 credits
    credits = int(total_cost * 100000)
    
    return credits

def record_usage(user_id, credits_used, usage_type, model_id=None, message_id=None, prompt_tokens=None, completion_tokens=None):
    """
    Record usage for credit tracking.
    
    Args:
        user_id (int): User ID
        credits_used (int): Credits used
        usage_type (str): Type of usage (e.g., "chat", "embedding")
        model_id (str, optional): Model ID
        message_id (int, optional): Message ID
        prompt_tokens (int, optional): Prompt tokens
        completion_tokens (int, optional): Completion tokens
    """
    try:
        # Create usage record
        usage = Usage(
            user_id=user_id,
            credits_used=credits_used,
            usage_type=usage_type,
            model_id=model_id,
            message_id=message_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        db.session.add(usage)
        
        # Deduct credits from user account
        user = User.query.get(user_id)
        if user:
            user.deduct_credits(credits_used)
        
        db.session.commit()
        
        return True
    
    except Exception as e:
        logger.error(f"Error recording usage: {e}")
        db.session.rollback()
        return False

def check_sufficient_credits(user_id, estimated_credits):
    """
    Check if user has sufficient credits for an operation.
    
    Args:
        user_id (int): User ID
        estimated_credits (int): Estimated credits needed
        
    Returns:
        bool: True if sufficient credits, False otherwise
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            logger.error(f"User {user_id} not found")
            return False
        
        # Check if user has free credits remaining
        return user.credits >= estimated_credits
    
    except Exception as e:
        logger.error(f"Error checking sufficient credits: {e}")
        return False

def is_free_model(model_id):
    """
    Determine if a model is free or paid.
    
    Args:
        model_id (str): The model ID to check
        
    Returns:
        bool: True if the model is free, False if it's paid
    """
    try:
        # First check: If the model ID contains the ':free' suffix
        if ':free' in model_id.lower():
            return True
            
        # Second check: Known free models (hardcoded to avoid circular imports)
        KNOWN_FREE_MODELS = [
            'google/gemini-2.0-flash-exp:free',
            'google/gemini-flash-1.5:free',
            'mistralai/mistral-7b-instruct:free',
            'huggingface/microsoft/dialoGPT-medium:free',
            'meta-llama/llama-3.2-1b-instruct:free',
            'meta-llama/llama-3.2-3b-instruct:free',
            'qwen/qwen-2-7b-instruct:free'
        ]
        
        if model_id in KNOWN_FREE_MODELS:
            return True
            
        # Third check: Try to get OpenRouter model info without circular import
        try:
            from models import OpenRouterModel
            db_model = OpenRouterModel.query.filter_by(model_id=model_id).first()
            if db_model and hasattr(db_model, 'is_free') and db_model.is_free:
                return True
        except Exception:
            # If database query fails, continue with other checks
            pass
                
        # Default to paid model if we can't determine otherwise
        return False
        
    except Exception as e:
        logger.error(f"Error checking if model {model_id} is free: {e}")
        # Default to paid model on error to be safe
        return False

def check_user_can_use_paid_models(user_id):
    """
    Check if a user can use paid models (has positive credit balance).
    
    Args:
        user_id (int): User ID
        
    Returns:
        bool: True if user has positive balance, False otherwise
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            logger.error(f"User {user_id} not found")
            return False
        
        # User can use paid models if they have a positive balance
        return user.credits > 0
    
    except Exception as e:
        logger.error(f"Error checking user {user_id} paid model access: {e}")
        return False


def process_affiliate_commission(user_id, transaction):
    """
    Process affiliate commissions for a completed transaction.
    This implements a two-tier affiliate system with:
    - 10% commission for Level 1 affiliates (direct referrers)
    - 5% commission for Level 2 affiliates (referrers of direct referrers)
    - Commissions are only paid for 1 year after the customer's first purchase
    
    Args:
        user_id (int): The customer's user ID
        transaction (Transaction): The completed transaction
    
    Returns:
        bool: True if commissions were processed, False otherwise
    """
    try:
        # Step 1: Check if a commission already exists for this transaction to prevent duplicates
        existing_commission = Commission.query.filter_by(
            triggering_transaction_id=transaction.stripe_payment_intent
        ).first()
        
        if existing_commission:
            logger.info(f"Commission already exists for transaction {transaction.stripe_payment_intent}")
            return False
        
        # Step 2: Get the customer's referral information (L1 affiliate)
        customer_referral = CustomerReferral.query.filter_by(customer_user_id=user_id).first()
        
        if not customer_referral:
            # No referral found for this user
            logger.info(f"No referral found for user {user_id}")
            return False
        
        # Get the Level 1 (L1) referring user
        l1_user = User.query.get(customer_referral.referrer_user_id)
        
        if not l1_user or not l1_user.referral_code:
            # L1 referring user not found or doesn't have a referral code
            logger.info(f"L1 referring user {customer_referral.referrer_user_id} not found or doesn't have a referral code")
            return False
        
        # Current time for commission dates
        now = datetime.utcnow()
        
        # Step 3: Check if this is the first purchase that results in a commission 
        # and update the first_commissioned_purchase_at field if needed
        if not customer_referral.first_commissioned_purchase_at:
            logger.info(f"Setting first commissioned purchase date for customer {user_id} to {now}")
            customer_referral.first_commissioned_purchase_at = now
            db.session.add(customer_referral)
            
        # Step 4: Check if the transaction is within the one-year commission window
        if not customer_referral.is_within_commission_window(transaction.created_at or now):
            logger.info(f"Transaction outside of one-year commission window for user {user_id}")
            logger.info(f"First commission date: {customer_referral.first_commissioned_purchase_at}")
            logger.info(f"Transaction date: {transaction.created_at or now}")
            return False
            
        # Step 5: Calculate base amount in GBP
        # For simplicity, we're using the transaction amount directly
        # In a real app, you might want to convert from USD to GBP if needed
        amount_gbp = transaction.amount_usd
        
        # Step 6: Calculate and create L1 commission (10%)
        l1_commission_rate = 0.10  # 10%
        l1_commission_amount = round(amount_gbp * l1_commission_rate, 2)
        
        available_date = now + timedelta(days=30)  # Available after 30 days
        
        # Create L1 commission record
        l1_commission = Commission(
            user_id=l1_user.id,
            triggering_transaction_id=transaction.stripe_payment_intent,
            stripe_payment_status='succeeded',
            purchase_amount_base=amount_gbp,
            commission_rate=l1_commission_rate,
            commission_amount=l1_commission_amount,
            commission_level=1,  # Level 1
            status=CommissionStatus.HELD.value,
            commission_earned_date=now,
            commission_available_date=available_date
        )
        
        db.session.add(l1_commission)
        logger.info(f"Created L1 commission of £{l1_commission_amount} for user {l1_user.id}")
        
        # Step 7: Check if there's a Level 2 (L2) affiliate
        if l1_user.referred_by_user_id:
            # Get the L2 user (who referred the L1 user)
            l2_user = User.query.get(l1_user.referred_by_user_id)
            
            if l2_user and l2_user.referral_code:
                # Calculate and create L2 commission (5%)
                l2_commission_rate = 0.05  # 5%
                l2_commission_amount = round(amount_gbp * l2_commission_rate, 2)
                
                # Create L2 commission record
                l2_commission = Commission(
                    user_id=l2_user.id,
                    triggering_transaction_id=transaction.stripe_payment_intent,
                    stripe_payment_status='succeeded',
                    purchase_amount_base=amount_gbp,
                    commission_rate=l2_commission_rate,
                    commission_amount=l2_commission_amount,
                    commission_level=2,  # Level 2
                    status=CommissionStatus.HELD.value,
                    commission_earned_date=now,
                    commission_available_date=available_date
                )
                
                db.session.add(l2_commission)
                logger.info(f"Created L2 commission of £{l2_commission_amount} for user {l2_user.id}")
        
        # Commit all changes
        db.session.commit()
        return True
    
    except Exception as e:
        logger.error(f"Error processing affiliate commission: {e}")
        db.session.rollback()  # Rollback transaction on error
        return False