"""
PayPal Payouts Module

This module handles PayPal payout functionality for affiliate commissions.
It uses the PayPal REST SDK to process batch payments to affiliates.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import PayPal configuration
from paypal_config import is_paypal_initialized, create_payout, get_payout_details

def process_payout_batch(affiliate_payouts):
    """
    Process a batch of payouts to affiliates using PayPal REST SDK
    
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
    if not is_paypal_initialized():
        return {
            'success': False,
            'error': 'PayPal is not initialized. Please check your PayPal configuration.'
        }
    
    try:
        # Prepare the batch
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        batch_id = f"AFFBATCH_{timestamp}"
        email_subject = "You've received a commission payment"
        email_message = "Thank you for being an affiliate. Your commission has been processed."
        
        # Create the payout items
        items = []
        commission_map = {}  # Maps sender_item_id to commission_id
        item_results = []
        
        for affiliate_id, payout_info in affiliate_payouts.items():
            try:
                # Process each commission as a separate payout item
                for commission_id in payout_info['commission_ids']:
                    amount_value = payout_info['amount']
                    recipient_email = payout_info['paypal_email']
                    sender_item_id = f"AFFCOM_{commission_id}_{timestamp}"
                    note = f"Commission payment for affiliate ID {affiliate_id}"
                    
                    # Map the sender_item_id to commission_id for later status updates
                    commission_map[sender_item_id] = commission_id
                    
                    # Create a payout item
                    payout_item = {
                        "recipient_type": "EMAIL",
                        "amount": {
                            "value": str(amount_value),
                            "currency": "GBP"
                        },
                        "note": note,
                        "sender_item_id": sender_item_id,
                        "receiver": recipient_email
                    }
                    
                    items.append(payout_item)
                    
                    # Track the item result for commission status updates
                    item_results.append({
                        'commission_id': commission_id,
                        'status': 'PENDING',
                        'error': None
                    })
            except Exception as e:
                logger.error(f"Error creating payout item for affiliate {affiliate_id}: {e}")
                continue
        
        if not items:
            return {
                'success': False,
                'error': 'No valid payout items could be created'
            }
        
        # Create the payout
        result = create_payout(sender_batch_id=batch_id, 
                              email_subject=email_subject, 
                              email_message=email_message, 
                              items=items)
        
        if result.get('success'):
            batch_id = result.get('batch_id')
            batch_status = result.get('batch_status')
            
            logger.info(f"Payout batch created with ID: {batch_id}, Status: {batch_status}")
            
            return {
                'success': True,
                'batch_id': batch_id,
                'batch_status': batch_status,
                'items_processed': items,
                'item_results': item_results,
                'commission_map': commission_map
            }
        else:
            error = result.get('error', 'Unknown error')
            logger.error(f"Error creating payout: {error}")
            return {
                'success': False,
                'error': f"PayPal error: {error}"
            }
    
    except Exception as e:
        logger.error(f"Unexpected error in process_payout_batch: {e}")
        return {
            'success': False,
            'error': f"Unexpected error: {str(e)}"
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
    if not is_paypal_initialized():
        return {
            'success': False,
            'error': 'PayPal is not initialized. Please check your PayPal configuration.'
        }
    
    try:
        # Get payout details
        result = get_payout_details(batch_id)
        
        if result.get('success'):
            batch_status = result.get('batch_status')
            
            logger.info(f"Payout batch {batch_id} status: {batch_status}")
            
            # Get the item details
            items = []
            for item in result.get('items', []):
                payout_item = item.get('payout_item', {})
                sender_item_id = payout_item.get('sender_item_id')
                
                item_data = {
                    'transaction_id': item.get('transaction_id'),
                    'transaction_status': item.get('transaction_status'),
                    'sender_item_id': sender_item_id,
                    'amount': payout_item.get('amount', {}).get('value'),
                    'currency': payout_item.get('amount', {}).get('currency'),
                    'receiver': payout_item.get('receiver'),
                    'status': item.get('transaction_status')
                }
                
                # Map to commission ID if available
                if commission_map and sender_item_id in commission_map:
                    item_data['commission_id'] = commission_map[sender_item_id]
                
                items.append(item_data)
            
            return {
                'success': True,
                'batch_id': batch_id,
                'batch_status': batch_status,
                'items': items
            }
        else:
            error = result.get('error', 'Unknown error')
            logger.error(f"Error getting payout details: {error}")
            return {
                'success': False,
                'error': f"PayPal error: {error}"
            }
    
    except Exception as e:
        logger.error(f"Unexpected error in get_payout_batch_status: {e}")
        return {
            'success': False,
            'error': f"Unexpected error: {str(e)}"
        }