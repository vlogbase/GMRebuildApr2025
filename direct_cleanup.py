#!/usr/bin/env python3
"""
Direct Database Cleanup for Empty Conversations

This script connects directly to the database to safely remove empty conversations
without loading the full Flask application.

Safety checks:
- Only removes conversations marked as inactive (is_active = false)  
- Verifies zero messages with multiple methods
- Requires conversations be older than 24 hours
- Dry run mode by default
"""

import os
import psycopg2
from datetime import datetime, timedelta
import argparse

def get_database_connection():
    """Get direct database connection"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    return psycopg2.connect(database_url)

def safe_cleanup_empty_conversations(dry_run=True):
    """
    Safely cleanup empty conversations with multiple validation checks
    """
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Calculate cutoff time (24 hours ago)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        print(f"Starting safe conversation cleanup (dry_run={dry_run})")
        print(f"Cutoff time: {cutoff_time}")
        
        # Find inactive conversations older than 24 hours
        cursor.execute("""
            SELECT id, title, user_id, created_at 
            FROM conversation 
            WHERE is_active = false 
            AND created_at < %s
            ORDER BY created_at
        """, (cutoff_time,))
        
        candidates = cursor.fetchall()
        print(f"Found {len(candidates)} inactive conversations older than 24 hours")
        
        safe_to_delete = []
        
        for conv_id, title, user_id, created_at in candidates:
            # Multiple validation checks
            
            # Check 1: Count messages
            cursor.execute("SELECT COUNT(*) FROM message WHERE conversation_id = %s", (conv_id,))
            message_count = cursor.fetchone()[0]
            
            # Check 2: Verify conversation is still inactive
            cursor.execute("""
                SELECT id FROM conversation 
                WHERE id = %s AND is_active = false
            """, (conv_id,))
            still_inactive = cursor.fetchone()
            
            # Safety validation
            if message_count == 0 and still_inactive:
                age_hours = (datetime.utcnow() - created_at).total_seconds() / 3600
                
                safe_to_delete.append({
                    'id': conv_id,
                    'title': title,
                    'user_id': user_id,
                    'age_hours': age_hours
                })
                
                print(f"✓ Conversation {conv_id} '{title}' is safe to delete: "
                      f"0 messages, inactive, {age_hours:.1f} hours old")
            else:
                print(f"✗ Conversation {conv_id} failed safety checks: "
                      f"messages={message_count}, still_inactive={bool(still_inactive)}")
        
        print(f"Identified {len(safe_to_delete)} conversations safe for deletion")
        
        if dry_run:
            print("DRY RUN MODE - No actual deletions performed")
            for conv in safe_to_delete:
                print(f"Would delete: ID {conv['id']}, Title: '{conv['title']}', "
                      f"User: {conv['user_id']}, Age: {conv['age_hours']:.1f}h")
        else:
            # Perform actual deletion with final safety check
            deleted_count = 0
            for conv_info in safe_to_delete:
                # Final verification before deletion
                cursor.execute("""
                    SELECT COUNT(*) FROM message WHERE conversation_id = %s
                """, (conv_info['id'],))
                final_message_check = cursor.fetchone()[0]
                
                if final_message_check == 0:
                    cursor.execute("""
                        DELETE FROM conversation 
                        WHERE id = %s AND is_active = false
                    """, (conv_info['id'],))
                    
                    if cursor.rowcount > 0:
                        deleted_count += 1
                        print(f"Deleted conversation {conv_info['id']}: '{conv_info['title']}'")
                    else:
                        print(f"Conversation {conv_info['id']} was not deleted (may have changed)")
                else:
                    print(f"SAFETY ABORT: Conversation {conv_info['id']} now has {final_message_check} messages!")
            
            if deleted_count > 0:
                conn.commit()
                print(f"Successfully deleted {deleted_count} empty conversations")
            else:
                print("No conversations were deleted")
        
        return {
            'total_candidates': len(candidates),
            'safe_to_delete': len(safe_to_delete),
            'deleted': 0 if dry_run else len([c for c in safe_to_delete]),
            'dry_run': dry_run
        }
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Safe conversation cleanup')
    parser.add_argument('--execute', action='store_true', 
                       help='Actually perform deletions (default is dry-run)')
    
    args = parser.parse_args()
    
    try:
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
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())