"""
Optimized Startup Module

This module provides a streamlined startup sequence for autoscaling environments.
It replaces heavy initialization tasks with lightweight health checks and 
defers system-wide tasks to singleton background workers.
"""

import os
import time
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

def fast_startup_sequence() -> Dict[str, Any]:
    """
    Execute the optimized startup sequence for fast instance startup.
    
    This replaces the old background_initializer setup with a much faster
    approach that only does essential per-instance setup.
    
    Returns:
        Dict with startup results and timing
    """
    start_time = time.time()
    results = {
        'database_health': False,
        'redis_connection': False,
        'singleton_worker': False,
        'azure_storage_deferred': True,  # Deferred to background
        'startup_time': 0,
        'success': False
    }
    
    try:
        logger.info("🚀 Starting optimized startup sequence...")
        
        # Step 1: Quick database health check (no migrations)
        try:
            from app_initialization import check_database_health
            db_result = check_database_health()
            results['database_health'] = db_result.get('success', False)
            
            if results['database_health']:
                logger.info("✓ Database health check passed")
            else:
                logger.warning(f"⚠️ Database health check failed: {db_result.get('message', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"✗ Database health check error: {e}")
            results['database_health'] = False
        
        # Step 2: Test Redis connection (non-blocking)
        try:
            from api_cache import get_redis_client
            redis_client = get_redis_client()
            if redis_client:
                # Quick ping test
                redis_client.ping()
                results['redis_connection'] = True
                logger.info("✓ Redis connection established")
            else:
                logger.info("ℹ️ Redis not available - will use fallback caching")
                results['redis_connection'] = False
                
        except Exception as e:
            logger.info(f"ℹ️ Redis connection failed (will use fallbacks): {e}")
            results['redis_connection'] = False
        
        # Step 3: Start singleton background worker (lightweight)
        try:
            from singleton_background_worker import start_singleton_worker
            worker = start_singleton_worker()
            results['singleton_worker'] = True
            logger.info("✓ Singleton background worker started")
            
        except Exception as e:
            logger.warning(f"⚠️ Singleton worker startup failed: {e}")
            results['singleton_worker'] = False
        
        # Calculate startup time
        results['startup_time'] = time.time() - start_time
        
        # Determine overall success
        # Only require database health - other services can fail gracefully
        results['success'] = results['database_health']
        
        if results['success']:
            logger.info(f"🎉 Optimized startup completed in {results['startup_time']:.2f}s")
        else:
            logger.error(f"❌ Startup failed after {results['startup_time']:.2f}s")
            
        return results
        
    except Exception as e:
        results['startup_time'] = time.time() - start_time
        logger.error(f"💥 Critical startup error: {e}")
        return results

def setup_essential_services_only():
    """
    Set up only the essential services required for immediate application functionality.
    
    This replaces the old setup_background_initialization() with a much lighter approach.
    
    Returns:
        Dict with setup results
    """
    try:
        logger.info("Setting up essential services for fast startup...")
        
        # Run the fast startup sequence
        results = fast_startup_sequence()
        
        if results['success']:
            logger.info("Essential services setup completed successfully")
        else:
            logger.warning("Some services failed during setup - application may have reduced functionality")
            
        return results
        
    except Exception as e:
        logger.error(f"Error setting up essential services: {e}")
        return {
            'success': False,
            'error': str(e),
            'startup_time': 0
        }

def get_startup_status() -> Dict[str, Any]:
    """
    Get the current status of startup components for health checks.
    
    Returns:
        Dict with current status of all startup components
    """
    status = {
        'database': 'unknown',
        'redis': 'unknown',
        'singleton_worker': 'unknown',
        'overall_health': 'unknown'
    }
    
    try:
        # Check database
        from app_initialization import check_database_health
        db_result = check_database_health()
        status['database'] = 'healthy' if db_result.get('success') else 'unhealthy'
        
        # Check Redis
        try:
            from api_cache import get_redis_client
            redis_client = get_redis_client()
            if redis_client:
                redis_client.ping()
                status['redis'] = 'connected'
            else:
                status['redis'] = 'disconnected'
        except:
            status['redis'] = 'disconnected'
            
        # Check singleton worker
        try:
            from singleton_background_worker import get_singleton_worker
            worker = get_singleton_worker()
            worker_status = worker.get_status()
            status['singleton_worker'] = 'running' if worker_status.get('running') else 'stopped'
        except:
            status['singleton_worker'] = 'unknown'
            
        # Determine overall health
        if status['database'] == 'healthy':
            status['overall_health'] = 'healthy'
        else:
            status['overall_health'] = 'unhealthy'
            
    except Exception as e:
        logger.error(f"Error getting startup status: {e}")
        status['overall_health'] = 'error'
        
    return status

# Health check endpoint data for monitoring
def get_health_check_data() -> Dict[str, Any]:
    """
    Get comprehensive health check data for monitoring and load balancing.
    
    Returns:
        Dict suitable for health check endpoints
    """
    startup_status = get_startup_status()
    
    return {
        'status': startup_status['overall_health'],
        'timestamp': time.time(),
        'services': {
            'database': startup_status['database'],
            'redis': startup_status['redis'],
            'background_worker': startup_status['singleton_worker']
        },
        'ready': startup_status['overall_health'] == 'healthy'
    }