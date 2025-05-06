"""
PayPal Payouts Module

This module handles PayPal payout functionality for affiliate commissions.
It uses the PayPal Payouts API to process batch payments to affiliates.
"""

import os
import logging
import json
from datetime import datetime
import uuid
from paypal.payouts import (
    PayoutsPostRequest,
    PayoutSenderBatchHeader, 
    SenderBatchHeader, 
    PayoutItem, 
    Amount,
    PayoutItemDetail
)
from paypal.payouts import PayoutsGetRequest
from paypal_config import get_paypal_client
from paypal.http import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_payout_batch(affiliate_payouts):
    """
    Process a batch of payouts to affiliates using PayPal Payouts API
    
    Args:
        affiliate_payouts (dict): Dictionary of affiliate payouts
            {
                affiliate_id: {
                    'paypal_email': 'email@example.com',
                    'amount': 25.50,
                    'commission_ids': [1, 2, 3]
                },
                ...
            }
    
    Returns:
        dict: Result of the payout operation
            {
                'success': True/False,
                'batch_id': 'PAYPAL_BATCH_ID',
                'items_processed': [],
                'error': 'Error message',
                'item_results': [{'commission_id': 123, 'status': 'PENDING', 'error': None}, ...],
                'commission_map': {sender_item_id: commission_id, ...}
            }
    """
    try:
        # Check if we have payouts to process
        if not affiliate_payouts:
            return {
                'success': False,
                'error': 'No valid payouts to process'
            }
        
        # Get PayPal client
        client = get_paypal_client()
        if not client:
            return {
                'success': False,
                'error': 'PayPal client initialization failed'
            }
        
        # Generate a unique batch ID
        sender_batch_id = f"AFFPAY_{uuid.uuid4().hex[:10]}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Create sender batch header
        sender_batch_header = SenderBatchHeader(
            sender_batch_id=sender_batch_id,
            email_subject="You received an affiliate commission payment"
        )
        
        # Create payout items array and commission map
        payout_items = []
        commission_map = {}  # Map sender_item_id to commission_id for tracking
        item_info = []  # Store information about created items
        
        for affiliate_id, data in affiliate_payouts.items():
            paypal_email = data['paypal_email']
            total_amount = data['amount']
            commission_ids = data['commission_ids']
            
            # Skip invalid amounts
            if total_amount <= 0:
                continue
            
            # Create a unique sender_item_id for each commission
            # This is crucial for tracking the success/failure of individual commissions
            for commission_id in commission_ids:
                # Calculate amount for this specific commission
                amount_per_commission = total_amount / len(commission_ids)
                
                # Create unique sender_item_id that includes the commission ID for tracking
                sender_item_id = f"AFFCOM_{commission_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                commission_map[sender_item_id] = commission_id
                
                # Create amount object
                amount = Amount(
                    currency="GBP",
                    value=f"{amount_per_commission:.2f}"
                )
                
                # Create payout item
                payout_item = PayoutItem(
                    receiver=paypal_email,
                    amount=amount,
                    sender_item_id=sender_item_id,
                    recipient_type="EMAIL",
                    note=f"Affiliate commission payout for commission #{commission_id}"
                )
                
                payout_items.append(payout_item)
                
                # Store information for result
                item_info.append({
                    'commission_id': commission_id,
                    'amount': amount_per_commission,
                    'paypal_email': paypal_email,
                    'sender_item_id': sender_item_id
                })
        
        # Skip if no valid items
        if not payout_items:
            return {
                'success': False,
                'error': 'No valid payout items to process'
            }
        
        # Create payout request
        request = PayoutsPostRequest()
        request.request_body(
            sender_batch_header=sender_batch_header,
            items=payout_items
        )
        
        try:
            # Call API with created request
            response = client.execute(request)
            
            # Process response
            batch_id = response.result.batch_header.payout_batch_id
            batch_status = response.result.batch_header.batch_status
            
            logger.info(f"Payout batch created with ID: {batch_id}, status: {batch_status}")
            
            # Prepare item results (all in PENDING state initially since we use async payout)
            item_results = []
            for item in item_info:
                item_results.append({
                    'commission_id': item['commission_id'],
                    'sender_item_id': item['sender_item_id'],
                    'status': 'PENDING',  # Initial status
                    'error': None
                })
            
            return {
                'success': True,
                'batch_id': batch_id,
                'batch_status': batch_status,
                'items_processed': item_info,
                'item_results': item_results,
                'commission_map': commission_map
            }
        
        except HttpError as http_error:
            # Handle HTTP errors from PayPal API
            error_data = http_error.message
            logger.error(f"PayPal API error: {error_data}")
            return {
                'success': False,
                'error': f"PayPal API error: {error_data}"
            }
        
    except Exception as e:
        logger.error(f"Error processing payout batch: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def get_payout_batch_status(batch_id, commission_map=None):
    """
    Get the status of a payout batch, including individual item statuses
    
    Args:
        batch_id (str): PayPal payout batch ID
        commission_map (dict, optional): Map of sender_item_id to commission_id
    
    Returns:
        dict: Payout batch status with item details
    """
    try:
        # Get PayPal client
        client = get_paypal_client()
        if not client:
            return {
                'success': False,
                'error': 'PayPal client initialization failed'
            }
        
        # Create request to get payout batch details
        request = PayoutsGetRequest(batch_id)
        
        try:
            # Call API with created request
            response = client.execute(request)
            
            # Process response
            batch_header = response.result.batch_header
            batch_status = batch_header.batch_status
            time_created = batch_header.time_created
            time_completed = getattr(batch_header, 'time_completed', None)
            
            # Extract item details
            items = response.result.items if hasattr(response.result, 'items') else []
            item_count = len(items)
            
            # Process individual items
            item_details = []
            for item in items:
                sender_item_id = getattr(item, 'payout_item.sender_item_id', None)
                if not sender_item_id and hasattr(item, 'payout_item'):
                    sender_item_id = getattr(item.payout_item, 'sender_item_id', None)
                
                commission_id = None
                if commission_map and sender_item_id in commission_map:
                    commission_id = commission_map[sender_item_id]
                
                # Get transaction status
                transaction_status = getattr(item, 'transaction_status', 'UNKNOWN')
                if not transaction_status and hasattr(item, 'payout_item_response'):
                    transaction_status = getattr(item.payout_item_response, 'transaction_status', 'UNKNOWN')
                
                # Get transaction ID
                transaction_id = getattr(item, 'transaction_id', None)
                if not transaction_id and hasattr(item, 'payout_item_response'):
                    transaction_id = getattr(item.payout_item_response, 'transaction_id', None)
                
                # Check for errors
                item_error = None
                if hasattr(item, 'errors') and item.errors:
                    error_details = []
                    for error in item.errors:
                        error_detail = {
                            'name': getattr(error, 'name', 'Unknown error'),
                            'message': getattr(error, 'message', 'No message available')
                        }
                        error_details.append(error_detail)
                    item_error = error_details
                
                item_details.append({
                    'commission_id': commission_id,
                    'sender_item_id': sender_item_id,
                    'status': transaction_status,
                    'transaction_id': transaction_id,
                    'error': item_error
                })
            
            return {
                'success': True,
                'batch_status': batch_status,
                'time_created': time_created,
                'time_completed': time_completed,
                'item_count': item_count,
                'items': item_details
            }
        
        except HttpError as http_error:
            # Handle HTTP errors from PayPal API
            error_data = http_error.message
            logger.error(f"PayPal API error getting batch status: {error_data}")
            return {
                'success': False,
                'error': f"PayPal API error: {error_data}"
            }
        
    except Exception as e:
        logger.error(f"Error getting payout batch status: {e}")
        return {
            'success': False,
            'error': str(e)
        }