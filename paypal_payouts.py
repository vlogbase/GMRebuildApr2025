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
                'error': 'Error message'
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
        
        for affiliate_id, data in affiliate_payouts.items():
            paypal_email = data['paypal_email']
            amount = data['amount']
            
            # Skip invalid amounts
            if amount <= 0:
                continue
            
            # Create payout item (all payouts are in GBP)
            payout_items.append({
                "recipient_type": "EMAIL",
                "amount": {
                    "value": str(amount),
                    "currency": "GBP"
                },
                "note": "Affiliate commission payout",
                "sender_item_id": f"AFFCOM_{affiliate_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
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
        
        # Process the payout
        if payout.create(sync_mode=False):
            logger.info(f"Payout created with batch ID: {payout.batch_header.payout_batch_id}")
            return {
                'success': True,
                'batch_id': payout.batch_header.payout_batch_id,
                'items_processed': payout_items
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

def get_payout_batch_status(batch_id):
    """
    Get the status of a payout batch
    
    Args:
        batch_id (str): PayPal payout batch ID
    
    Returns:
        dict: Payout batch status
    """
    try:
        # Get payout batch
        payout_batch = Payout.find(batch_id)
        
        if payout_batch:
            return {
                'success': True,
                'batch_status': payout_batch.batch_header.batch_status,
                'time_created': payout_batch.batch_header.time_created,
                'time_completed': payout_batch.batch_header.time_completed,
                'item_count': len(payout_batch.items) if hasattr(payout_batch, 'items') else 0
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