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

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify, g
from flask_login import current_user, login_required
from sqlalchemy import desc, func, and_

from app import db
from models import User, Transaction, Usage, Package, PaymentStatus
from models import CustomerReferral, Affiliate, Commission, CommissionStatus, AffiliateStatus
from stripe_config import initialize_stripe, create_checkout_session, verify_webhook_signature

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
        # Get packages
        packages = Package.query.filter_by(is_active=True).all()
        
        # Get recent transactions
        recent_transactions = Transaction.query.filter_by(user_id=current_user.id) \
            .order_by(desc(Transaction.created_at)).limit(5).all()
        
        # Get recent usage
        recent_usage = Usage.query.filter_by(user_id=current_user.id) \
            .order_by(desc(Usage.created_at)).limit(5).all()
        
        # Get affiliate information
        affiliate = Affiliate.query.filter_by(email=current_user.email).first()
        
        # If the user doesn't have an affiliate record, auto-create one
        if not affiliate:
            affiliate = Affiliate.auto_create_for_user(current_user)
            
        # Get commission statistics if affiliate exists and is active
        commission_stats = {}
        if affiliate and affiliate.status == AffiliateStatus.ACTIVE.value:
            # Get total earned commissions
            earned_commissions = db.session.query(func.sum(Commission.commission_amount)).filter(
                Commission.affiliate_id == affiliate.id,
                Commission.status.in_([CommissionStatus.APPROVED.value, CommissionStatus.PAID.value])
            ).scalar() or 0
            
            # Get pending commissions
            pending_commissions = db.session.query(func.sum(Commission.commission_amount)).filter(
                Commission.affiliate_id == affiliate.id,
                Commission.status == CommissionStatus.HELD.value
            ).scalar() or 0
            
            # Get referral count
            referral_count = CustomerReferral.query.filter_by(affiliate_id=affiliate.id).count()
            
            commission_stats = {
                'total_earned': f'${earned_commissions:.2f}',
                'pending': f'${pending_commissions:.2f}',
                'referrals': referral_count
            }
        
        return render_template(
            'account.html',
            user=current_user,
            packages=packages,
            recent_transactions=recent_transactions,
            recent_usage=recent_usage,
            affiliate=affiliate,
            commission_stats=commission_stats
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
        # Get all usage records
        usage_list = Usage.query.filter_by(user_id=current_user.id) \
            .order_by(desc(Usage.created_at)).all()
        
        return render_template(
            'usage_history.html',
            usage_list=usage_list
        )
    
    except Exception as e:
        logger.error(f"Error in usage_history: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('billing.account_management'))

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


def process_affiliate_commission(user_id, transaction):
    """
    Process affiliate commissions for a completed transaction.
    This implements a two-tier affiliate system with:
    - 10% commission for Level 1 affiliates (direct referrers)
    - 5% commission for Level 2 affiliates (referrers of direct referrers)
    
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
        
        # Get the Level 1 (L1) affiliate
        l1_affiliate = Affiliate.query.get(customer_referral.affiliate_id)
        
        if not l1_affiliate or l1_affiliate.status != 'active':
            # L1 affiliate not found or not active
            logger.info(f"L1 affiliate {customer_referral.affiliate_id} not found or not active")
            return False
        
        # Step 3: Calculate base amount in GBP
        # For simplicity, we're using the transaction amount directly
        # In a real app, you might want to convert from USD to GBP if needed
        amount_gbp = transaction.amount_usd
        
        # Step 4: Calculate and create L1 commission (10%)
        l1_commission_rate = 0.10  # 10%
        l1_commission_amount = round(amount_gbp * l1_commission_rate, 2)
        
        # Current time for commission dates
        now = datetime.utcnow()
        available_date = now + timedelta(days=30)  # Available after 30 days
        
        # Create L1 commission record
        l1_commission = Commission(
            affiliate_id=l1_affiliate.id,
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
        logger.info(f"Created L1 commission of £{l1_commission_amount} for affiliate {l1_affiliate.id}")
        
        # Step 5: Check if there's a Level 2 (L2) affiliate
        if l1_affiliate.referred_by_affiliate_id:
            # Get the L2 affiliate
            l2_affiliate = Affiliate.query.get(l1_affiliate.referred_by_affiliate_id)
            
            if l2_affiliate and l2_affiliate.status == 'active':
                # Calculate and create L2 commission (5%)
                l2_commission_rate = 0.05  # 5%
                l2_commission_amount = round(amount_gbp * l2_commission_rate, 2)
                
                # Create L2 commission record
                l2_commission = Commission(
                    affiliate_id=l2_affiliate.id,
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
                logger.info(f"Created L2 commission of £{l2_commission_amount} for affiliate {l2_affiliate.id}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error processing affiliate commission: {e}")
        return False