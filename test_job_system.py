#!/usr/bin/env python
"""
Comprehensive Job System Test

This script tests the entire job processing system by:
1. Creating job queues
2. Adding test jobs to the queues
3. Starting a worker in the same process
4. Processing the jobs
5. Verifying results
"""

import os
import sys
import time
import logging
import json
import uuid
import datetime
from redis import Redis
from rq import Queue, Worker
import ssl
from redis.connection import SSLConnection, ConnectionPool

# Import job functions from a separate module
# This is critical for RQ to work properly
from test_job_functions import (
    example_email_job,
    example_report_job,
    example_processing_job, 
    example_cache_update_job,
    example_long_task
)

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
    """Get a connection to Redis"""
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

def setup_job_queues():
    """Set up job queues"""
    redis_conn = get_redis_connection()
    
    # Define queues
    queues = {
        "high": Queue("high", connection=redis_conn),
        "default": Queue("default", connection=redis_conn),
        "low": Queue("low", connection=redis_conn),
        "email": Queue("email", connection=redis_conn),
        "indexing": Queue("indexing", connection=redis_conn)
    }
    
    # Clear existing jobs for testing
    for queue in queues.values():
        queue.empty()
    
    return queues, redis_conn

def add_test_jobs(queues):
    """Add test jobs to the queues"""
    jobs = []
    
    # Add email job to email queue
    job = queues["email"].enqueue(
        example_email_job,
        "test@example.com",
        "Test Email",
        "This is a test email body",
        job_id=f"email_job_{uuid.uuid4()}"
    )
    jobs.append(job)
    logger.info(f"Added email job: {job.id}")
    
    # Add report job to high queue
    job = queues["high"].enqueue(
        example_report_job,
        123,
        "monthly",
        job_id=f"report_job_{uuid.uuid4()}"
    )
    jobs.append(job)
    logger.info(f"Added report job: {job.id}")
    
    # Add processing job to default queue
    job = queues["default"].enqueue(
        example_processing_job,
        "/tmp/test.pdf",
        456,
        job_id=f"processing_job_{uuid.uuid4()}"
    )
    jobs.append(job)
    logger.info(f"Added processing job: {job.id}")
    
    # Add cache update job to low queue
    job = queues["low"].enqueue(
        example_cache_update_job,
        789,
        job_id=f"cache_job_{uuid.uuid4()}"
    )
    jobs.append(job)
    logger.info(f"Added cache update job: {job.id}")
    
    # Add long task to indexing queue
    job = queues["indexing"].enqueue(
        example_long_task,
        3,  # 3 seconds
        job_id=f"long_task_{uuid.uuid4()}"
    )
    jobs.append(job)
    logger.info(f"Added long task job: {job.id}")
    
    return jobs

def process_jobs(queues, redis_conn):
    """Process jobs with a worker"""
    # Create a temporary worker to process jobs
    worker_name = f"test_worker_{uuid.uuid4()}"
    
    # Create worker with all queues
    worker = Worker(
        queues=list(queues.values()),
        name=worker_name,
        connection=redis_conn
    )
    
    logger.info(f"Starting worker {worker_name} to process jobs")
    
    # Process jobs for a limited time
    # (In a real app, this would run continuously)
    worker.work(burst=True)  # Burst mode - process jobs then exit
    
    logger.info("Worker finished processing jobs")

def check_job_results(jobs):
    """Check the results of processed jobs"""
    succeeded = 0
    failed = 0
    
    for job in jobs:
        # Refresh job state from Redis
        job.refresh()
        
        if job.is_finished:
            succeeded += 1
            logger.info(f"Job {job.id} succeeded with result: {job.result}")
        elif job.is_failed:
            failed += 1
            logger.error(f"Job {job.id} failed with error: {job.exc_info}")
        else:
            logger.warning(f"Job {job.id} is still in state: {job.get_status()}")
    
    logger.info(f"Job processing summary: {succeeded} succeeded, {failed} failed")
    return succeeded, failed

def run_job_system_test():
    """Run a complete test of the job system"""
    logger.info("Starting comprehensive job system test")
    
    # Setup queues
    queues, redis_conn = setup_job_queues()
    
    # Add test jobs
    jobs = add_test_jobs(queues)
    
    # Process the jobs
    process_jobs(queues, redis_conn)
    
    # Check results
    succeeded, failed = check_job_results(jobs)
    
    # Final summary
    total = len(jobs)
    logger.info(f"Test complete: {succeeded}/{total} jobs succeeded, {failed}/{total} jobs failed")
    
    return succeeded == total  # True if all jobs succeeded

if __name__ == "__main__":
    success = run_job_system_test()
    sys.exit(0 if success else 1)