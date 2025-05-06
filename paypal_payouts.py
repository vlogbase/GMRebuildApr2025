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

import paypalrestsdk
from paypalrestsdk import Payout

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
                'items_processed': [item1, item2, ...],
                'error': 'Error message',
                'item_results': [{'commission_id': 123, 'status': 'SUCCESS', 'error': None}, ...]
            }
    """
    try:
        # Check if we have payouts to process
        if not affiliate_payouts:
            return {
                'success': False,
                'error': 'No valid payouts to process'
            }
        
        # Generate a unique batch ID
        sender_batch_id = f"AFFPAY_{uuid.uuid4().hex[:10]}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Create the payout items
        payout_items = []
        commission_map = {}  # Map sender_item_id to commission IDs for tracking
        
        for affiliate_id, data in affiliate_payouts.items():
            paypal_email = data['paypal_email']
            amount = data['amount']
            commission_ids = data['commission_ids']
            
            # Skip invalid amounts
            if amount <= 0:
                continue
            
            # Create a unique sender_item_id for each commission
            # This is crucial for tracking the success/failure of each individual commission
            for commission_id in commission_ids:
                sender_item_id = f"AFFCOM_{commission_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                commission_map[sender_item_id] = commission_id
                
                # Create payout item (all payouts are in GBP)
                payout_items.append({
                    "recipient_type": "EMAIL",
                    "amount": {
                        "value": str(amount / len(commission_ids)),  # Divide the amount equally among commissions
                        "currency": "GBP"
                    },
                    "note": f"Affiliate commission payout for commission #{commission_id}",
                    "sender_item_id": sender_item_id,
                    "receiver": paypal_email
                })
        
        # Skip if no valid items
        if not payout_items:
            return {
                'success': False,
                'error': 'No valid payout items to process'
            }
        
        # Create the payout
        payout = Payout({
            "sender_batch_header": {
                "sender_batch_id": sender_batch_id,
                "email_subject": "You received an affiliate commission payment"
            },
            "items": payout_items
        })
        
        # Process the payout and track individual item results
        if payout.create(sync_mode=False):  # Using sync_mode=True would wait for results
            logger.info(f"Payout batch created with ID: {payout.batch_header.payout_batch_id}")
            
            # Get detailed payout information
            # For item-level status, we'll need to retrieve the batch later with get_payout_batch_status
            item_results = []
            for item in payout_items:
                sender_item_id = item['sender_item_id']
                commission_id = commission_map.get(sender_item_id)
                item_results.append({
                    'commission_id': commission_id,
                    'sender_item_id': sender_item_id,
                    'status': 'PENDING',  # Initial status is pending since we use async payout
                    'error': None
                })
            
            return {
                'success': True,
                'batch_id': payout.batch_header.payout_batch_id,
                'items_processed': payout_items,
                'item_results': item_results,
                'commission_map': commission_map
            }
        else:
            logger.error(f"Payout creation failed: {payout.error}")
            return {
                'success': False,
                'error': f"Payout creation failed: {json.dumps(payout.error)}"
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
        # Get payout batch
        payout_batch = Payout.find(batch_id)
        
        if payout_batch:
            # Extract item status details
            item_details = []
            if hasattr(payout_batch, 'items'):
                for item in payout_batch.items:
                    sender_item_id = getattr(item, 'sender_item_id', 'unknown')
                    commission_id = None
                    if commission_map and sender_item_id in commission_map:
                        commission_id = commission_map[sender_item_id]
                    
                    item_status = getattr(item, 'transaction_status', 'UNKNOWN')
                    item_error = None
                    
                    # Check for errors
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
                        'status': item_status,
                        'transaction_id': getattr(item, 'transaction_id', None),
                        'error': item_error
                    })
            
            return {
                'success': True,
                'batch_status': payout_batch.batch_header.batch_status,
                'time_created': payout_batch.batch_header.time_created,
                'time_completed': getattr(payout_batch.batch_header, 'time_completed', None),
                'item_count': len(payout_batch.items) if hasattr(payout_batch, 'items') else 0,
                'items': item_details
            }
        else:
            return {
                'success': False,
                'error': 'Payout batch not found'
            }
    
    except Exception as e:
        logger.error(f"Error getting payout batch status: {e}")
        return {
            'success': False,
            'error': str(e)
        }