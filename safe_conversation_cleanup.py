#!/usr/bin/env python3
"""
Safe Conversation Cleanup Script

This script identifies and removes only conversations that are:
1. Marked as inactive (is_active = false)
2. Have zero messages
3. Are older than 24 hours
4. Multiple validation checks to prevent false positives

Safety measures:
- Only processes inactive conversations
- Verifies zero message count from multiple angles
- Age requirement prevents accidental deletion of new conversations
- Dry-run mode by default
- Detailed logging of all actions
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def safe_cleanup_empty_conversations(dry_run=True):
    """
    Safely cleanup empty conversations with multiple validation checks
    
    Args:
        dry_run (bool): If True, only report what would be deleted without actually deleting
    
    Returns:
        dict: Summary of cleanup results
    """
    try:
        from app import db
        from models import Conversation, Message
        
        # Safety threshold: only process conversations older than 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        logger.info(f"Starting safe conversation cleanup (dry_run={dry_run})")
        logger.info(f"Cutoff time: {cutoff_time}")
        
        # Find conversations that meet ALL safety criteria
        candidates = db.session.query(Conversation).filter(
            Conversation.is_active == False,  # Must be inactive
            Conversation.created_at < cutoff_time  # Must be older than 24 hours
        ).all()
        
        logger.info(f"Found {len(candidates)} inactive conversations older than 24 hours")
        
        safe_to_delete = []
        
        for conv in candidates:
            # Multiple validation checks for each conversation
            
            # Check 1: Count messages using SQLAlchemy
            message_count_1 = db.session.query(Message).filter_by(conversation_id=conv.id).count()
            
            # Check 2: Count messages using raw SQL for verification
            result = db.session.execute(
                "SELECT COUNT(*) FROM message WHERE conversation_id = :conv_id",
                {"conv_id": conv.id}
            )
            message_count_2 = result.scalar()
            
            # Check 3: Verify conversation still exists and is inactive
            conv_check = db.session.query(Conversation).filter_by(
                id=conv.id, 
                is_active=False
            ).first()
            
            # Safety validation: all checks must pass
            if (message_count_1 == 0 and 
                message_count_2 == 0 and 
                conv_check is not None and
                conv.created_at < cutoff_time):
                
                safe_to_delete.append({
                    'id': conv.id,
                    'title': conv.title,
                    'user_id': conv.user_id,
                    'created_at': conv.created_at,
                    'age_hours': (datetime.utcnow() - conv.created_at).total_seconds() / 3600
                })
                
                logger.info(f"✓ Conversation {conv.id} '{conv.title}' is safe to delete: "
                           f"0 messages, inactive, {(datetime.utcnow() - conv.created_at).total_seconds() / 3600:.1f} hours old")
            else:
                logger.warning(f"✗ Conversation {conv.id} failed safety checks: "
                             f"msg_count_1={message_count_1}, msg_count_2={message_count_2}, "
                             f"exists={conv_check is not None}, age_ok={conv.created_at < cutoff_time}")
        
        logger.info(f"Identified {len(safe_to_delete)} conversations safe for deletion")
        
        if dry_run:
            logger.info("DRY RUN MODE - No actual deletions performed")
            for conv in safe_to_delete:
                logger.info(f"Would delete: ID {conv['id']}, Title: '{conv['title']}', "
                           f"User: {conv['user_id']}, Age: {conv['age_hours']:.1f}h")
        else:
            # Perform actual deletion with final safety check
            deleted_count = 0
            for conv_info in safe_to_delete:
                # Final verification before deletion
                conv = db.session.query(Conversation).filter_by(
                    id=conv_info['id'],
                    is_active=False
                ).first()
                
                if conv:
                    final_message_check = db.session.query(Message).filter_by(
                        conversation_id=conv.id
                    ).count()
                    
                    if final_message_check == 0:
                        db.session.delete(conv)
                        deleted_count += 1
                        logger.info(f"Deleted conversation {conv.id}: '{conv.title}'")
                    else:
                        logger.error(f"SAFETY ABORT: Conversation {conv.id} now has {final_message_check} messages!")
                else:
                    logger.warning(f"Conversation {conv_info['id']} no longer exists or became active")
            
            if deleted_count > 0:
                db.session.commit()
                logger.info(f"Successfully deleted {deleted_count} empty conversations")
            else:
                logger.info("No conversations were deleted")
        
        return {
            'total_candidates': len(candidates),
            'safe_to_delete': len(safe_to_delete),
            'deleted': 0 if dry_run else len(safe_to_delete),
            'dry_run': dry_run,
            'conversations': safe_to_delete
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        if not dry_run:
            db.session.rollback()
        raise

def main():
    """Run the cleanup with dry-run mode by default"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Safe conversation cleanup')
    parser.add_argument('--execute', action='store_true', 
                       help='Actually perform deletions (default is dry-run)')
    
    args = parser.parse_args()
    
    # Run cleanup
    result = safe_cleanup_empty_conversations(dry_run=not args.execute)
    
    print("\n" + "="*50)
    print("CLEANUP SUMMARY")
    print("="*50)
    print(f"Mode: {'DRY RUN' if result['dry_run'] else 'EXECUTION'}")
    print(f"Total inactive conversations checked: {result['total_candidates']}")
    print(f"Safe to delete: {result['safe_to_delete']}")
    print(f"Actually deleted: {result['deleted']}")
    
    if result['safe_to_delete'] > 0 and result['dry_run']:
        print(f"\nTo actually delete these conversations, run:")
        print(f"python {__file__} --execute")

if __name__ == '__main__':
    main()