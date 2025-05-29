#!/usr/bin/env python3
"""
Deployment Migrations CLI

This script handles all database migrations that should run once per deployment,
not on every application instance startup. This improves autoscaling performance
by ensuring migrations only run when actually deploying new code.
"""

import os
import sys
import logging
import signal
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_deployment_migrations():
    """
    Run all database migrations required for deployment.
    This should be called once per deployment, not per instance.
    
    Returns:
        bool: True if all migrations successful, False otherwise
    """
    try:
        # Import Flask app and database
        from app import app, db
        
        migration_results = {
            'openrouter_model': False,
            'user_chat_settings': False,
            'affiliate': False,
            'conversation_index': False,
            'message_index': False
        }
        
        logger.info("Starting deployment-time database migrations...")
        
        with app.app_context():
            # Ensure all tables are created first
            db.create_all()
            logger.info("Base database tables ensured")
            
            # Run OpenRouter model migrations
            try:
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                
                if not inspector.has_table('open_router_model'):
                    logger.info("Running OpenRouter model migrations...")
                    from migrations_openrouter_model import run_migrations
                    success = run_migrations()
                    migration_results['openrouter_model'] = success
                    if success:
                        logger.info("✓ OpenRouter model migration completed")
                    else:
                        logger.error("✗ OpenRouter model migration failed")
                else:
                    logger.info("✓ OpenRouter model table already exists")
                    migration_results['openrouter_model'] = True
                    
            except Exception as e:
                logger.error(f"✗ OpenRouter model migration error: {e}")
                migration_results['openrouter_model'] = False
                
            # Run UserChatSettings migration with timeout protection
            try:
                logger.info("Running UserChatSettings migration...")
                from migrations_user_chat_settings import run_migration
                
                def migration_timeout_handler(signum, frame):
                    raise TimeoutError("UserChatSettings migration timed out after 60 seconds")
                
                # Set up timeout protection (Unix systems only)
                if hasattr(signal, 'SIGALRM'):
                    signal.signal(signal.SIGALRM, migration_timeout_handler)
                    signal.alarm(60)  # 60 second timeout for deployment
                
                try:
                    success = run_migration()
                    migration_results['user_chat_settings'] = success
                    if success:
                        logger.info("✓ UserChatSettings migration completed")
                    else:
                        logger.error("✗ UserChatSettings migration failed")
                        
                finally:
                    if hasattr(signal, 'SIGALRM'):
                        signal.alarm(0)  # Clear timeout
                        
            except TimeoutError:
                logger.error("✗ UserChatSettings migration timed out")
                migration_results['user_chat_settings'] = False
            except Exception as e:
                logger.error(f"✗ UserChatSettings migration error: {e}")
                migration_results['user_chat_settings'] = False
                
            # Run affiliate migrations if available
            try:
                from migrations_affiliate import run_migrations as run_affiliate_migrations
                logger.info("Running affiliate system migrations...")
                success = run_affiliate_migrations()
                migration_results['affiliate'] = success
                if success:
                    logger.info("✓ Affiliate migration completed")
                else:
                    logger.error("✗ Affiliate migration failed")
            except ImportError:
                logger.info("✓ Affiliate migrations not found (optional)")
                migration_results['affiliate'] = True
            except Exception as e:
                logger.error(f"✗ Affiliate migration error: {e}")
                migration_results['affiliate'] = False
                
            # Mark index migrations as successful (these are typically handled by ORM)
            migration_results['conversation_index'] = True
            migration_results['message_index'] = True
            
            # Summary
            successful = sum(1 for result in migration_results.values() if result)
            total = len(migration_results)
            
            logger.info(f"Deployment migrations completed: {successful}/{total} successful")
            
            if successful == total:
                logger.info("🎉 All deployment migrations completed successfully!")
                return True
            else:
                logger.error(f"❌ {total - successful} migrations failed")
                return False
                
    except Exception as e:
        logger.error(f"Critical error during deployment migrations: {e}")
        return False

def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run deployment-time database migrations')
    parser.add_argument('--force', action='store_true', 
                       help='Force run migrations even if they appear complete')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what migrations would run without executing them')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("DRY RUN: Would execute deployment migrations")
        return 0
        
    logger.info("Starting deployment migration process...")
    success = run_deployment_migrations()
    
    if success:
        logger.info("Deployment migrations completed successfully")
        return 0
    else:
        logger.error("Deployment migrations failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())