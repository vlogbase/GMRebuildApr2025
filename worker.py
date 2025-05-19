"""
Redis Queue (RQ) Worker Configuration for GloriaMundo Chatbot

This module defines the RQ worker configuration for processing background jobs.
"""

import os
import logging
import redis
from rq import Worker, Queue
from redis_cache import redis_cache

logger = logging.getLogger(__name__)

def get_redis_connection():
    """
    Get a Redis connection for RQ workers
    
    Returns:
        redis.Redis: A Redis connection instance
    """
    return redis_cache.get_redis()

def create_worker(queues=None, name=None):
    """
    Create an RQ worker to process jobs from the specified queues
    
    Args:
        queues (list, optional): List of queue names to process jobs from.
                               If None, processes jobs from all queues.
        name (str, optional): Name for the worker
                            
    Returns:
        Worker: An RQ worker instance
    """
    from jobs import queues as available_queues
    
    if queues is None:
        # Use all available queues if none specified
        queue_instances = list(available_queues.values())
    else:
        # Use only the specified queues
        queue_instances = [available_queues.get(q) for q in queues if q in available_queues]
    
    if not queue_instances:
        logger.warning("No valid queues specified, using default queue")
        queue_instances = [available_queues.get('default')]
    
    connection = get_redis_connection()
    
    worker = Worker(
        queues=queue_instances,
        connection=connection,
        name=name
    )
    
    return worker