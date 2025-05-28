"""
Diagnostic Version of Background Tasks with Enhanced Logging

This script adds comprehensive logging to identify exactly where the hang occurs
in the database migrations process.
"""

import logging
import time
import sys
import threading
from datetime import datetime

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def diagnostic_database_migrations():
    """
    Diagnostic version of database migrations with step-by-step logging
    """
    logger.info("🔍 DIAGNOSTIC: Starting database migrations diagnosis")
    
    try:
        logger.info("🔍 DIAGNOSTIC: Step 1 - Importing Flask app and db")
        from app import app, db
        logger.info("✅ DIAGNOSTIC: Successfully imported app and db")
        
        logger.info("🔍 DIAGNOSTIC: Step 2 - Creating Flask app context")
        with app.app_context():
            logger.info("✅ DIAGNOSTIC: Flask app context created successfully")
            
            logger.info("🔍 DIAGNOSTIC: Step 3 - Importing sqlalchemy inspect")
            from sqlalchemy import inspect
            logger.info("✅ DIAGNOSTIC: SQLAlchemy inspect imported")
            
            logger.info("🔍 DIAGNOSTIC: Step 4 - Creating database inspector")
            inspector = inspect(db.engine)
            logger.info("✅ DIAGNOSTIC: Database inspector created")
            
            logger.info("🔍 DIAGNOSTIC: Step 5 - Checking if open_router_model table exists")
            has_table = inspector.has_table('open_router_model')
            logger.info(f"✅ DIAGNOSTIC: Table check complete - exists: {has_table}")
            
            if not has_table:
                logger.info("🔍 DIAGNOSTIC: Step 6a - Table missing, importing migration module")
                try:
                    from migrations_openrouter_model import run_migrations
                    logger.info("✅ DIAGNOSTIC: Migration module imported successfully")
                    
                    logger.info("🔍 DIAGNOSTIC: Step 6b - Executing run_migrations()")
                    success = run_migrations()
                    logger.info(f"✅ DIAGNOSTIC: Migration execution complete - success: {success}")
                except Exception as e:
                    logger.error(f"❌ DIAGNOSTIC: Error in OpenRouter migration: {e}")
                    return {'success': False, 'error': str(e), 'step': 'openrouter_migration'}
            else:
                logger.info("🔍 DIAGNOSTIC: Step 6 - Table exists, skipping OpenRouter migration")
            
            logger.info("🔍 DIAGNOSTIC: Step 7 - Starting UserChatSettings migration")
            try:
                from migrations_user_chat_settings import run_migration
                logger.info("✅ DIAGNOSTIC: UserChatSettings migration module imported")
                
                logger.info("🔍 DIAGNOSTIC: Step 7a - Executing UserChatSettings migration")
                success = run_migration()
                logger.info(f"✅ DIAGNOSTIC: UserChatSettings migration complete - success: {success}")
            except Exception as e:
                logger.error(f"❌ DIAGNOSTIC: Error in UserChatSettings migration: {e}")
                return {'success': False, 'error': str(e), 'step': 'user_chat_settings_migration'}
            
            logger.info("🔍 DIAGNOSTIC: Step 8 - All migrations completed successfully")
            
        logger.info("✅ DIAGNOSTIC: Database migrations diagnosis completed successfully")
        return {'success': True, 'completed_at': datetime.now().isoformat()}
        
    except Exception as e:
        logger.error(f"❌ DIAGNOSTIC: Critical error in migrations: {e}")
        import traceback
        logger.error(f"❌ DIAGNOSTIC: Full traceback: {traceback.format_exc()}")
        return {'success': False, 'error': str(e), 'step': 'critical_error'}

def diagnostic_openrouter_api():
    """
    Diagnostic test of OpenRouter API call to identify network-related hangs
    """
    logger.info("🔍 DIAGNOSTIC: Testing OpenRouter API connectivity")
    
    try:
        import os
        import requests
        
        api_key = os.environ.get('OPENROUTER_API_KEY')
        logger.info(f"🔍 DIAGNOSTIC: API key present: {bool(api_key)}")
        
        if not api_key:
            logger.warning("⚠️ DIAGNOSTIC: No API key found - skipping API test")
            return {'success': True, 'skipped': True, 'reason': 'no_api_key'}
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        logger.info("🔍 DIAGNOSTIC: Making API request with 10-second timeout")
        start_time = time.time()
        
        response = requests.get(
            'https://openrouter.ai/api/v1/models',
            headers=headers,
            timeout=10.0
        )
        
        elapsed = time.time() - start_time
        logger.info(f"✅ DIAGNOSTIC: API call completed in {elapsed:.2f}s - Status: {response.status_code}")
        
        return {'success': True, 'status_code': response.status_code, 'response_time': elapsed}
        
    except Exception as e:
        logger.error(f"❌ DIAGNOSTIC: API test failed: {e}")
        return {'success': False, 'error': str(e)}

def run_diagnostic():
    """
    Run comprehensive diagnostic of background tasks
    """
    logger.info("🚀 Starting comprehensive background task diagnostics")
    
    # Test 1: Database migrations
    logger.info("=" * 50)
    logger.info("TEST 1: Database Migrations Diagnostic")
    logger.info("=" * 50)
    
    start_time = time.time()
    db_result = diagnostic_database_migrations()
    db_time = time.time() - start_time
    
    logger.info(f"Database migrations test completed in {db_time:.2f}s")
    logger.info(f"Result: {db_result}")
    
    # Test 2: OpenRouter API
    logger.info("=" * 50)
    logger.info("TEST 2: OpenRouter API Diagnostic")
    logger.info("=" * 50)
    
    start_time = time.time()
    api_result = diagnostic_openrouter_api()
    api_time = time.time() - start_time
    
    logger.info(f"API test completed in {api_time:.2f}s")
    logger.info(f"Result: {api_result}")
    
    # Summary
    logger.info("=" * 50)
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Database migrations: {'✅ PASS' if db_result['success'] else '❌ FAIL'} ({db_time:.2f}s)")
    logger.info(f"OpenRouter API: {'✅ PASS' if api_result['success'] else '❌ FAIL'} ({api_time:.2f}s)")
    
    if not db_result['success']:
        logger.error(f"Database migration failed at step: {db_result.get('step', 'unknown')}")
        logger.error(f"Error: {db_result.get('error', 'unknown')}")
    
    if not api_result['success'] and not api_result.get('skipped'):
        logger.error(f"API test failed: {api_result.get('error', 'unknown')}")
    
    return {
        'database_migrations': db_result,
        'openrouter_api': api_result,
        'total_time': db_time + api_time
    }

if __name__ == "__main__":
    result = run_diagnostic()
    print("\n" + "=" * 60)
    print("FINAL DIAGNOSTIC RESULTS")
    print("=" * 60)
    print(f"Overall success: {result['database_migrations']['success'] and result['openrouter_api']['success']}")
    print(f"Total execution time: {result['total_time']:.2f} seconds")