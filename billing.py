"""
Billing Module for GloriaMundo Chatbot

This module handles billing routes, account management, and credit purchases.
It provides endpoints for:
1. Account management page
2. Credit purchase through PayPal
3. Credit usage tracking
"""

import os
import logging
import math
from datetime import datetime
from urllib.parse import urlparse

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify
from flask_login import current_user, login_required
from sqlalchemy import desc
import paypalrestsdk

from app import db
from models import User, Transaction, Usage, Package, PaymentStatus
from paypal_config import initialize_paypal, create_payment, execute_payment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
billing_bp = Blueprint('billing', __name__)

# Initialize PayPal
initialize_paypal()

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
        
        return render_template(
            'account.html',
            user=current_user,
            packages=packages,
            recent_transactions=recent_transactions,
            recent_usage=recent_usage
        )
    
    except Exception as e:
        logger.error(f"Error in account_management: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('index'))

@billing_bp.route('/purchase/<int:package_id>', methods=['POST'])
@login_required
def purchase_package(package_id):
    """
    Initiate a credit package purchase.
    
    Args:
        package_id: ID of the package to purchase
    """
    try:
        # Get package
        package = Package.query.get(package_id)
        if not package:
            flash("Invalid package selected", "error")
            return redirect(url_for('billing.account_management'))
        
        # Create return URLs
        base_url = request.host_url.rstrip('/')
        return_url = f"{base_url}{url_for('billing.execute_purchase', package_id=package_id)}"
        cancel_url = f"{base_url}{url_for('billing.cancel_purchase')}"
        
        # Create PayPal payment
        payment_result = create_payment(
            amount_usd=package.amount_usd,
            return_url=return_url,
            cancel_url=cancel_url,
            package_name=package.name
        )
        
        if payment_result["success"]:
            # Create transaction record
            transaction = Transaction(
                user_id=current_user.id,
                package_id=package.id,
                amount_usd=package.amount_usd,
                credits=package.credits,
                payment_method="paypal",
                payment_id=payment_result["payment_id"],
                status=PaymentStatus.PENDING.value
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Redirect to PayPal approval URL
            return redirect(payment_result["approval_url"])
        else:
            flash(f"Error creating PayPal payment: {payment_result.get('error', 'Unknown error')}", "error")
            return redirect(url_for('billing.account_management'))
    
    except Exception as e:
        logger.error(f"Error in purchase_package: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('billing.account_management'))

@billing_bp.route('/purchase/custom', methods=['POST'])
@login_required
def purchase_custom():
    """
    Process a custom amount credit purchase.
    """
    try:
        # Get amount
        amount_usd = float(request.form.get('amount', 0))
        
        # Validate amount
        if amount_usd < 1.00 or amount_usd > 100.00:
            flash("Invalid amount. Please enter an amount between $1.00 and $100.00", "error")
            return redirect(url_for('billing.account_management'))
        
        # Calculate credits to give (base credits + bonus)
        # More generous bonus for higher amounts
        base_credits = int(amount_usd * 1000)  # 1 credit = $0.001 ($1 = 1000 credits)
        
        if amount_usd >= 50:
            bonus_percentage = 30  # 30% bonus for $50+
        elif amount_usd >= 25:
            bonus_percentage = 20  # 20% bonus for $25-49.99
        elif amount_usd >= 10:
            bonus_percentage = 10  # 10% bonus for $10-24.99
        else:
            bonus_percentage = 0  # No bonus for small amounts
        
        bonus_credits = int(base_credits * (bonus_percentage / 100))
        total_credits = base_credits + bonus_credits
        
        # Create return URLs
        base_url = request.host_url.rstrip('/')
        return_url = f"{base_url}{url_for('billing.execute_custom_purchase')}"
        cancel_url = f"{base_url}{url_for('billing.cancel_purchase')}"
        
        # Create PayPal payment
        package_name = f"Custom ${amount_usd:.2f} Credit Purchase"
        payment_result = create_payment(
            amount_usd=amount_usd,
            return_url=return_url,
            cancel_url=cancel_url,
            package_name=package_name
        )
        
        if payment_result["success"]:
            # Store payment details in session for processing after return
            session['custom_payment'] = {
                'payment_id': payment_result["payment_id"],
                'amount_usd': amount_usd,
                'credits': total_credits
            }
            
            # Create transaction record
            transaction = Transaction(
                user_id=current_user.id,
                package_id=None,
                amount_usd=amount_usd,
                credits=total_credits,
                payment_method="paypal",
                payment_id=payment_result["payment_id"],
                status=PaymentStatus.PENDING.value
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Redirect to PayPal approval URL
            return redirect(payment_result["approval_url"])
        else:
            flash(f"Error creating PayPal payment: {payment_result.get('error', 'Unknown error')}", "error")
            return redirect(url_for('billing.account_management'))
    
    except Exception as e:
        logger.error(f"Error in purchase_custom: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('billing.account_management'))

@billing_bp.route('/execute/<int:package_id>', methods=['GET'])
@login_required
def execute_purchase(package_id):
    """
    Execute a credit package purchase after PayPal approval.
    
    Args:
        package_id: ID of the package being purchased
    """
    try:
        # Get PayPal parameters
        payment_id = request.args.get('paymentId')
        payer_id = request.args.get('PayerID')
        
        if not payment_id or not payer_id:
            flash("Invalid payment parameters", "error")
            return redirect(url_for('billing.account_management'))
        
        # Get package
        package = Package.query.get(package_id)
        if not package:
            flash("Invalid package", "error")
            return redirect(url_for('billing.account_management'))
        
        # Get transaction
        transaction = Transaction.query.filter_by(
            user_id=current_user.id, 
            payment_id=payment_id,
            status=PaymentStatus.PENDING.value
        ).first()
        
        if not transaction:
            flash("Transaction not found", "error")
            return redirect(url_for('billing.account_management'))
        
        # Execute PayPal payment
        result = execute_payment(payment_id, payer_id)
        
        if result["success"]:
            # Update transaction status
            transaction.status = PaymentStatus.COMPLETED.value
            transaction.updated_at = datetime.utcnow()
            
            # Add credits to user account
            current_user.add_credits(transaction.credits)
            
            # Save changes
            db.session.commit()
            
            # Success message
            flash(f"Purchase successful! {transaction.credits} credits have been added to your account.", "success")
        else:
            # Update transaction status
            transaction.status = PaymentStatus.FAILED.value
            transaction.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Error message
            flash(f"Payment execution failed: {result.get('error', 'Unknown error')}", "error")
        
        return redirect(url_for('billing.account_management'))
    
    except Exception as e:
        logger.error(f"Error in execute_purchase: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('billing.account_management'))

@billing_bp.route('/execute/custom', methods=['GET'])
@login_required
def execute_custom_purchase():
    """
    Execute a custom amount credit purchase after PayPal approval.
    """
    try:
        # Get PayPal parameters
        payment_id = request.args.get('paymentId')
        payer_id = request.args.get('PayerID')
        
        if not payment_id or not payer_id:
            flash("Invalid payment parameters", "error")
            return redirect(url_for('billing.account_management'))
        
        # Get transaction
        transaction = Transaction.query.filter_by(
            user_id=current_user.id, 
            payment_id=payment_id,
            status=PaymentStatus.PENDING.value
        ).first()
        
        if not transaction:
            flash("Transaction not found", "error")
            return redirect(url_for('billing.account_management'))
        
        # Execute PayPal payment
        result = execute_payment(payment_id, payer_id)
        
        if result["success"]:
            # Update transaction status
            transaction.status = PaymentStatus.COMPLETED.value
            transaction.updated_at = datetime.utcnow()
            
            # Add credits to user account
            current_user.add_credits(transaction.credits)
            
            # Save changes
            db.session.commit()
            
            # Success message
            flash(f"Purchase successful! {transaction.credits} credits have been added to your account.", "success")
        else:
            # Update transaction status
            transaction.status = PaymentStatus.FAILED.value
            transaction.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Error message
            flash(f"Payment execution failed: {result.get('error', 'Unknown error')}", "error")
        
        # Clear session data
        if 'custom_payment' in session:
            del session['custom_payment']
        
        return redirect(url_for('billing.account_management'))
    
    except Exception as e:
        logger.error(f"Error in execute_custom_purchase: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('billing.account_management'))

@billing_bp.route('/cancel', methods=['GET'])
@login_required
def cancel_purchase():
    """
    Handle cancelled PayPal payments.
    """
    try:
        payment_id = request.args.get('paymentId')
        
        if payment_id:
            # Update transaction status
            transaction = Transaction.query.filter_by(
                user_id=current_user.id, 
                payment_id=payment_id,
                status=PaymentStatus.PENDING.value
            ).first()
            
            if transaction:
                transaction.status = PaymentStatus.FAILED.value
                transaction.updated_at = datetime.utcnow()
                db.session.commit()
        
        # Clear session data
        if 'custom_payment' in session:
            del session['custom_payment']
        
        flash("Payment cancelled", "info")
        return redirect(url_for('billing.account_management'))
    
    except Exception as e:
        logger.error(f"Error in cancel_purchase: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('billing.account_management'))

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

def calculate_openrouter_credits(prompt_tokens, completion_tokens, model_cost_per_million):
    """
    Calculate credits used for an OpenRouter request.
    
    Args:
        prompt_tokens (int): Number of prompt tokens
        completion_tokens (int): Number of completion tokens
        model_cost_per_million (float): Model cost per million tokens in USD
        
    Returns:
        int: Credits used
    """
    # Calculate token cost
    token_cost = model_cost_per_million / 1000000  # Cost per token
    
    # Calculate total cost
    total_cost = (prompt_tokens * token_cost) + (completion_tokens * token_cost)
    
    # Apply markup (2x)
    total_cost_with_markup = total_cost * 2
    
    # Convert to credits (1 credit = $0.001)
    # $1 = 1,000 credits
    credits = int(total_cost_with_markup * 1000)
    
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
    
    # Convert to credits (1 credit = $0.001)
    # $1 = 1,000 credits
    credits = int(total_cost * 1000)
    
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