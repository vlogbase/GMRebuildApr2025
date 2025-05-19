#!/usr/bin/env python
"""
Test Job Queue Script

This script adds test jobs to the Redis queue for processing by the job workers.
It helps verify that the background job processing system is working correctly.
"""

import os
import sys
import time
import logging
import datetime
from redis import Redis
from rq import Queue
from rq.job import Job
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Redis connection parameters
REDIS_HOST = 'my-bullmq-cache.redis.cache.windows.net'
REDIS_PORT = 6380
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
REDIS_SSL = True

def get_redis_connection():
    """Get a connection to Redis using SSL for Azure Redis Cache"""
    try:
        # Configure SSL connection for Azure Redis Cache
        import ssl
        
        # Use SSL connection via ConnectionPool
        from redis.connection import SSLConnection, ConnectionPool
        pool = ConnectionPool(
            connection_class=SSLConnection,
            host=REDIS_HOST,
            port=int(REDIS_PORT),
            password=REDIS_PASSWORD,
            socket_timeout=10,
            socket_connect_timeout=10,
            health_check_interval=30,
            ssl_cert_reqs=ssl.CERT_NONE
        )
        conn = Redis(connection_pool=pool, decode_responses=False)
        
        # Test the connection
        conn.ping()
        logger.info(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        return conn
    except Exception as e:
        logger.error(f"Unexpected error connecting to Redis: {str(e)}")
        raise

def add_test_jobs(count=5):
    """Add test jobs to the queue"""
    redis_conn = get_redis_connection()
    
    # Define example jobs
    job_functions = [
        ("jobs.send_email_notification", {"recipient_email": "test@example.com", 
                                         "subject": "Test Email", 
                                         "message": "This is a test email"}),
        ("jobs.generate_analytics_report", {"user_id": 123, 
                                           "report_type": "activity"}),
        ("jobs.update_user_cache", {"user_id": 456}),
        ("jobs.calculate_usage_statistics", {"start_date": "2025-01-01", 
                                            "end_date": "2025-05-19"}),
        ("jobs.long_running_task", {"duration": 5})
    ]
    
    queues = {
        "high": Queue("high", connection=redis_conn),
        "default": Queue("default", connection=redis_conn),
        "low": Queue("low", connection=redis_conn),
        "email": Queue("email", connection=redis_conn),
        "indexing": Queue("indexing", connection=redis_conn)
    }
    
    jobs = []
    
    # Queue distribution
    queue_mapping = {
        "jobs.send_email_notification": "email",
        "jobs.generate_analytics_report": "high",
        "jobs.update_user_cache": "default",
        "jobs.calculate_usage_statistics": "low",
        "jobs.long_running_task": "indexing"
    }
    
    logger.info(f"Adding {count} test jobs to queues")
    
    for i in range(count):
        # Select a job function with round-robin
        func_name, kwargs = job_functions[i % len(job_functions)]
        queue_name = queue_mapping.get(func_name, "default")
        
        try:
            # Add timestamp to make each job unique
            kwargs["timestamp"] = datetime.datetime.now().isoformat()
            
            # Enqueue the job
            queue = queues[queue_name]
            job = queue.enqueue(func_name, **kwargs, job_id=f"test_job_{i}_{int(time.time())}")
            
            jobs.append((job.id, queue_name, func_name))
            logger.info(f"Enqueued job {job.id} in {queue_name} queue: {func_name}")
            
        except Exception as e:
            logger.error(f"Error enqueueing job {func_name}: {str(e)}")
    
    # Return the job IDs and details
    return jobs

def monitor_jobs(job_ids, timeout=30):
    """Monitor the status of jobs until they complete or timeout"""
    redis_conn = get_redis_connection()
    
    start_time = time.time()
    pending_jobs = set(job_ids)
    
    logger.info(f"Monitoring {len(pending_jobs)} jobs for up to {timeout} seconds")
    
    while pending_jobs and (time.time() - start_time) < timeout:
        for job_id in list(pending_jobs):
            try:
                job = Job.fetch(job_id, connection=redis_conn)
                status = job.get_status()
                
                if status in ('finished', 'failed'):
                    pending_jobs.remove(job_id)
                    
                    if status == 'finished':
                        result = str(job.result)[:100] + "..." if len(str(job.result)) > 100 else str(job.result)
                        logger.info(f"Job {job_id} completed with result: {result}")
                    else:
                        logger.warning(f"Job {job_id} failed with error: {job.exc_info}")
            except Exception as e:
                logger.error(f"Error checking job {job_id}: {str(e)}")
                pending_jobs.remove(job_id)
        
        # If jobs are still pending, wait a bit
        if pending_jobs:
            time.sleep(1)
    
    # Check for remaining jobs
    if pending_jobs:
        logger.warning(f"{len(pending_jobs)} jobs did not complete within {timeout} seconds")
    else:
        logger.info(f"All jobs completed within {time.time() - start_time:.2f} seconds")

def check_queue_status():
    """Check the status of all queues"""
    redis_conn = get_redis_connection()
    
    queues = [
        Queue("high", connection=redis_conn),
        Queue("default", connection=redis_conn),
        Queue("low", connection=redis_conn),
        Queue("email", connection=redis_conn),
        Queue("indexing", connection=redis_conn)
    ]
    
    for queue in queues:
        job_count = len(queue)
        logger.info(f"Queue {queue.name}: {job_count} jobs")

def run_tests():
    """Run the job system tests"""
    logger.info("Starting job system tests")
    
    # Check queue status before adding jobs
    check_queue_status()
    
    # Add test jobs
    job_data = add_test_jobs(5)
    job_ids = [job[0] for job in job_data]
    
    # Monitor job completion
    monitor_jobs(job_ids, timeout=60)
    
    # Check queue status after processing
    check_queue_status()
    
    logger.info("Job system tests completed")

if __name__ == "__main__":
    run_tests()