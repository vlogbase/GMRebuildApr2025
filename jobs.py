"""
Jobs Module

This module provides a job system based on Redis Queue (RQ).
It allows for background processing of tasks and reduces load on the main application.
"""

import os
import time
import logging
import json
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps

import redis
from rq import Queue, Worker, job
from rq.job import Job, JobStatus
from rq.worker import Worker as RQWorker
from rq.registry import FailedJobRegistry, ScheduledJobRegistry, FinishedJobRegistry
from rq.exceptions import NoSuchJobError
from rq import Connection

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, scoped_session

from redis_cache import get_redis_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

class JobManager:
    """
    Manager for background jobs
    
    This class provides an interface for enqueuing and managing background jobs.
    """
    
    def __init__(self, queues=None, default_queue='default'):
        """
        Initialize the job manager
        
        Args:
            queues (dict, optional): Dictionary of queue names to create
                Example: {'default': {'ttl': 3600}, 'email': {'ttl': 7200}}
            default_queue (str): Default queue name to use if none specified
        """
        self.redis_conn = get_redis_connection()
        self.default_queue = default_queue
        
        # Default queues if none provided
        if queues is None:
            queues = {
                'high': {'ttl': 3600, 'result_ttl': 3600},
                'default': {'ttl': 3600, 'result_ttl': 3600},
                'low': {'ttl': 3600, 'result_ttl': 3600},
                'email': {'ttl': 7200, 'result_ttl': 3600},
                'indexing': {'ttl': 10800, 'result_ttl': 3600}
            }
        
        # Create queues
        self.queues = {}
        for queue_name, queue_config in queues.items():
            ttl = queue_config.get('ttl', 3600)
            result_ttl = queue_config.get('result_ttl', 3600)
            
            self.queues[queue_name] = Queue(
                name=queue_name,
                connection=self.redis_conn,
                default_timeout=ttl,
                result_ttl=result_ttl
            )
        
        # Ensure default queue exists
        if default_queue not in self.queues:
            self.queues[default_queue] = Queue(
                name=default_queue,
                connection=self.redis_conn,
                default_timeout=3600,
                result_ttl=3600
            )
        
        logger.info(f"Initialized job manager with queues: {', '.join(self.queues.keys())}")
    
    def get_queue(self, queue_name=None):
        """
        Get a queue by name
        
        Args:
            queue_name (str, optional): Queue name, or None for default queue
            
        Returns:
            Queue: The requested queue
        """
        if queue_name is None:
            queue_name = self.default_queue
        
        if queue_name not in self.queues:
            logger.warning(f"Queue {queue_name} not found, using default queue")
            queue_name = self.default_queue
        
        return self.queues[queue_name]
    
    def enqueue(self, func, *args, queue_name=None, depends_on=None, **kwargs):
        """
        Enqueue a job
        
        Args:
            func: The function to run
            *args: Arguments to pass to the function
            queue_name (str, optional): Queue name, or None for default queue
            depends_on (Job, optional): Job that must complete before this one
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Job: The enqueued job
        """
        queue = self.get_queue(queue_name)
        
        try:
            logger.info(f"Enqueuing job {func.__name__} to queue {queue.name}")
            
            # Get special RQ keyword arguments (if any)
            rq_kwargs = {}
            for key in ['timeout', 'result_ttl', 'ttl', 'failure_ttl', 'description', 
                        'meta', 'at_front', 'job_id', 'on_success', 'on_failure']:
                if key in kwargs:
                    rq_kwargs[key] = kwargs.pop(key)
            
            # Enqueue the job
            job = queue.enqueue(func, *args, depends_on=depends_on, **kwargs, **rq_kwargs)
            
            logger.info(f"Job {func.__name__} enqueued with ID {job.id}")
            return job
            
        except Exception as e:
            logger.error(f"Error enqueuing job {func.__name__}: {str(e)}")
            raise
    
    def enqueue_at(self, datetime_obj, func, *args, queue_name=None, **kwargs):
        """
        Enqueue a job to run at a specific time
        
        Args:
            datetime_obj (datetime): When to run the job
            func: The function to run
            *args: Arguments to pass to the function
            queue_name (str, optional): Queue name, or None for default queue
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Job: The enqueued job
        """
        queue = self.get_queue(queue_name)
        
        try:
            logger.info(f"Scheduling job {func.__name__} to run at {datetime_obj}")
            
            # Get special RQ keyword arguments (if any)
            rq_kwargs = {}
            for key in ['timeout', 'result_ttl', 'ttl', 'failure_ttl', 'description', 
                        'meta', 'job_id', 'on_success', 'on_failure']:
                if key in kwargs:
                    rq_kwargs[key] = kwargs.pop(key)
            
            # Enqueue the job
            job = queue.enqueue_at(datetime_obj, func, *args, **kwargs, **rq_kwargs)
            
            logger.info(f"Job {func.__name__} scheduled with ID {job.id}")
            return job
            
        except Exception as e:
            logger.error(f"Error scheduling job {func.__name__}: {str(e)}")
            raise
    
    def enqueue_in(self, timedelta_obj, func, *args, queue_name=None, **kwargs):
        """
        Enqueue a job to run after a time interval
        
        Args:
            timedelta_obj (timedelta): How long to wait before running the job
            func: The function to run
            *args: Arguments to pass to the function
            queue_name (str, optional): Queue name, or None for default queue
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Job: The enqueued job
        """
        queue = self.get_queue(queue_name)
        
        try:
            logger.info(f"Scheduling job {func.__name__} to run in {timedelta_obj}")
            
            # Get special RQ keyword arguments (if any)
            rq_kwargs = {}
            for key in ['timeout', 'result_ttl', 'ttl', 'failure_ttl', 'description', 
                        'meta', 'job_id', 'on_success', 'on_failure']:
                if key in kwargs:
                    rq_kwargs[key] = kwargs.pop(key)
            
            # Calculate the target datetime
            target_datetime = datetime.now() + timedelta_obj
            
            # Enqueue the job
            job = queue.enqueue_at(target_datetime, func, *args, **kwargs, **rq_kwargs)
            
            logger.info(f"Job {func.__name__} scheduled with ID {job.id}")
            return job
            
        except Exception as e:
            logger.error(f"Error scheduling job {func.__name__}: {str(e)}")
            raise
    
    def fetch_job(self, job_id):
        """
        Fetch a job by ID
        
        Args:
            job_id (str): The job ID
            
        Returns:
            Job: The job, or None if not found
        """
        try:
            return Job.fetch(job_id, connection=self.redis_conn)
        except NoSuchJobError:
            logger.warning(f"Job {job_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching job {job_id}: {str(e)}")
            return None
    
    def cancel_job(self, job_id):
        """
        Cancel a job by ID
        
        Args:
            job_id (str): The job ID
            
        Returns:
            bool: True if the job was cancelled, False otherwise
        """
        try:
            job = self.fetch_job(job_id)
            if job is None:
                return False
            
            cancelled = job.cancel()
            if cancelled:
                logger.info(f"Job {job_id} cancelled")
            else:
                logger.warning(f"Job {job_id} could not be cancelled (already started or finished)")
            
            return cancelled
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {str(e)}")
            return False
    
    def requeue_job(self, job_id):
        """
        Requeue a failed job
        
        Args:
            job_id (str): The job ID
            
        Returns:
            Job: The requeued job, or None if not found or not failed
        """
        try:
            job = self.fetch_job(job_id)
            if job is None:
                logger.warning(f"Job {job_id} not found for requeuing")
                return None
            
            if job.is_failed:
                logger.info(f"Requeuing failed job {job_id}")
                job.requeue()
                return job
            else:
                logger.warning(f"Job {job_id} is not failed, cannot requeue")
                return None
        except Exception as e:
            logger.error(f"Error requeuing job {job_id}: {str(e)}")
            return None
    
    def get_queue_stats(self, queue_name=None):
        """
        Get statistics for a queue
        
        Args:
            queue_name (str, optional): Queue name, or None for all queues
            
        Returns:
            dict: Queue statistics
        """
        if queue_name is not None:
            # Stats for a specific queue
            queue = self.get_queue(queue_name)
            
            # Get registries
            failed_registry = FailedJobRegistry(queue=queue)
            finished_registry = FinishedJobRegistry(queue=queue)
            scheduled_registry = ScheduledJobRegistry(queue=queue)
            
            return {
                'name': queue.name,
                'jobs': {
                    'queued': queue.count,
                    'failed': len(failed_registry),
                    'finished': len(finished_registry),
                    'scheduled': len(scheduled_registry),
                    'total': queue.count + len(failed_registry) + len(finished_registry) + len(scheduled_registry)
                }
            }
        else:
            # Stats for all queues
            stats = {
                'queues': [],
                'total_jobs': 0
            }
            
            for name, queue in self.queues.items():
                queue_stats = self.get_queue_stats(name)
                stats['queues'].append(queue_stats)
                stats['total_jobs'] += queue_stats['jobs']['total']
            
            return stats
    
    def get_active_workers(self):
        """
        Get active worker information
        
        Returns:
            list: List of active workers
        """
        try:
            workers = Worker.all(connection=self.redis_conn)
            
            worker_info = []
            for worker in workers:
                info = {
                    'name': worker.name,
                    'queues': [q.name for q in worker.queues],
                    'state': worker.state,
                    'current_job': None
                }
                
                # Get current job if any
                if worker.get_current_job():
                    job = worker.get_current_job()
                    info['current_job'] = {
                        'id': job.id,
                        'status': job.get_status(),
                        'description': job.description
                    }
                
                worker_info.append(info)
            
            return worker_info
        except Exception as e:
            logger.error(f"Error getting active workers: {str(e)}")
            return []
    
    def get_jobs(self, queue_name=None, status=None, start=0, end=100):
        """
        Get jobs from a queue
        
        Args:
            queue_name (str, optional): Queue name, or None for all queues
            status (str, optional): Job status to filter by (queued, started, finished, failed, scheduled, deferred)
            start (int): Start index for pagination
            end (int): End index for pagination
            
        Returns:
            list: List of jobs
        """
        try:
            if queue_name is not None:
                # Get jobs from a specific queue
                queue = self.get_queue(queue_name)
                
                if status == 'failed':
                    # Get failed jobs
                    registry = FailedJobRegistry(queue=queue)
                    job_ids = registry.get_job_ids(start, end)
                elif status == 'finished':
                    # Get finished jobs
                    registry = FinishedJobRegistry(queue=queue)
                    job_ids = registry.get_job_ids(start, end)
                elif status == 'scheduled':
                    # Get scheduled jobs
                    registry = ScheduledJobRegistry(queue=queue)
                    job_ids = registry.get_job_ids(start, end)
                elif status == 'started':
                    # Get started jobs
                    job_ids = [j.id for j in queue.started_job_registry.get_jobs(start, end)]
                elif status == 'deferred':
                    # Get deferred jobs
                    job_ids = [j.id for j in queue.deferred_job_registry.get_jobs(start, end)]
                else:
                    # Get queued jobs
                    job_ids = queue.get_job_ids(start, end)
                
                # Fetch job objects
                jobs = []
                for job_id in job_ids:
                    try:
                        job = Job.fetch(job_id, connection=self.redis_conn)
                        jobs.append(job)
                    except NoSuchJobError:
                        continue
                    except Exception as e:
                        logger.error(f"Error fetching job {job_id}: {str(e)}")
                        continue
                
                return jobs
            else:
                # Get jobs from all queues
                jobs = []
                for name in self.queues.keys():
                    jobs.extend(self.get_jobs(name, status, start, end))
                
                return jobs
        except Exception as e:
            logger.error(f"Error getting jobs: {str(e)}")
            return []
    
    def clear_queue(self, queue_name):
        """
        Remove all jobs from a queue
        
        Args:
            queue_name (str): Queue name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            queue = self.get_queue(queue_name)
            queue.empty()
            
            # Also clear registries
            FailedJobRegistry(queue=queue).empty()
            FinishedJobRegistry(queue=queue).empty()
            ScheduledJobRegistry(queue=queue).empty()
            
            logger.info(f"Queue {queue_name} cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing queue {queue_name}: {str(e)}")
            return False
    
    def background_job(self, queue_name=None, **rq_kwargs):
        """
        Decorator for background jobs
        
        Args:
            queue_name (str, optional): Queue name, or None for default queue
            **rq_kwargs: Additional RQ job options
            
        Returns:
            callable: Decorated function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Run the job immediately if RQ_ASYNC is disabled,
                # or if this code is running in an RQ worker
                # (i.e., this is already a background job)
                if (not os.environ.get('RQ_ASYNC', 'true').lower() in ('true', '1', 'yes')) or \
                   (hasattr(wrapper, 'job') and wrapper.job):
                    return func(*args, **kwargs)
                
                # Otherwise, enqueue the job
                return self.enqueue(func, *args, queue_name=queue_name, **kwargs, **rq_kwargs)
            
            # Store the queue name for use in the admin interface
            wrapper.queue_name = queue_name or self.default_queue
            wrapper.is_background_job = True
            
            return wrapper
        
        return decorator


def setup_database_session():
    """
    Set up a database session using SQLAlchemy
    
    Returns:
        Session: SQLAlchemy session
    """
    try:
        # Get database URL from environment
        database_url = os.environ.get("DATABASE_URL")
        
        if not database_url:
            logger.error("DATABASE_URL not set")
            return None
        
        # Create engine and session
        engine = create_engine(database_url, pool_recycle=300, pool_pre_ping=True)
        Session = scoped_session(sessionmaker(bind=engine))
        
        return Session()
    except Exception as e:
        logger.error(f"Error setting up database session: {str(e)}")
        return None


# Example job functions

def example_email_job(recipient, subject, body):
    """
    Example job for sending an email
    
    Args:
        recipient (str): Email recipient
        subject (str): Email subject
        body (str): Email body
    """
    logger.info(f"Sending email to {recipient} with subject '{subject}'")
    # In a real application, this would use an email library
    time.sleep(2)  # Simulate sending the email
    logger.info(f"Email sent to {recipient}")
    return {'status': 'sent', 'recipient': recipient, 'subject': subject}

def example_report_job(user_id, report_type):
    """
    Example job for generating a report
    
    Args:
        user_id (int): User ID
        report_type (str): Type of report to generate
    """
    logger.info(f"Generating {report_type} report for user {user_id}")
    
    # Simulate database access
    session = setup_database_session()
    if session is None:
        logger.error("Could not set up database session")
        return {'status': 'error', 'message': 'Database connection failed'}
    
    try:
        # Simulate report generation (would query the database in real code)
        time.sleep(3)
        
        # Generate a report object
        report = {
            'user_id': user_id,
            'type': report_type,
            'generated_at': datetime.now().isoformat(),
            'data': {
                'summary': 'Example report data',
                'details': [
                    {'item': 'Item 1', 'value': 100},
                    {'item': 'Item 2', 'value': 200},
                    {'item': 'Item 3', 'value': 300}
                ]
            }
        }
        
        logger.info(f"Report generated for user {user_id}")
        return {'status': 'success', 'report': report}
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return {'status': 'error', 'message': str(e)}
    finally:
        session.close()

def example_processing_job(data_id, options=None):
    """
    Example job for processing data
    
    Args:
        data_id (int): ID of data to process
        options (dict, optional): Processing options
    """
    if options is None:
        options = {}
    
    logger.info(f"Processing data {data_id} with options {options}")
    
    # Simulate processing steps
    steps = ['extract', 'transform', 'load']
    results = {}
    
    try:
        for step in steps:
            logger.info(f"Processing step: {step}")
            time.sleep(1)  # Simulate work
            results[step] = f"Completed {step} step for data {data_id}"
        
        logger.info(f"Data processing complete for {data_id}")
        return {'status': 'success', 'data_id': data_id, 'results': results}
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def example_cache_update_job(cache_key, new_value):
    """
    Example job for updating a cache
    
    Args:
        cache_key (str): Cache key to update
        new_value: New value to set
    """
    logger.info(f"Updating cache key {cache_key}")
    
    # Simulate cache update
    time.sleep(1)
    
    # In a real application, this would use a cache manager
    logger.info(f"Cache key {cache_key} updated")
    return {'status': 'success', 'cache_key': cache_key}

def example_long_task(duration=60, interval=5):
    """
    Example long-running task with progress updates
    
    Args:
        duration (int): Total duration in seconds
        interval (int): Progress update interval in seconds
    """
    logger.info(f"Starting long task (duration: {duration}s, interval: {interval}s)")
    
    # Get the job instance (if running in the background)
    try:
        job_instance = Job.fetch(job.get_current_job_id(), connection=get_redis_connection())
    except:
        job_instance = None
    
    start_time = time.time()
    end_time = start_time + duration
    
    try:
        while time.time() < end_time:
            elapsed = time.time() - start_time
            progress = min(100, round(elapsed / duration * 100, 1))
            
            # Update job meta with progress
            if job_instance:
                job_instance.meta['progress'] = progress
                job_instance.save_meta()
            
            logger.info(f"Long task progress: {progress}%")
            
            # Sleep for the interval or until the end time
            sleep_time = min(interval, end_time - time.time())
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        logger.info("Long task completed")
        return {'status': 'success', 'progress': 100}
    except Exception as e:
        logger.error(f"Error in long task: {str(e)}")
        return {'status': 'error', 'message': str(e)}


# Create global job manager instance
job_manager = JobManager()

# Export decorated example jobs
email_job = job_manager.background_job(queue_name='email')(example_email_job)
report_job = job_manager.background_job(queue_name='default')(example_report_job)
processing_job = job_manager.background_job(queue_name='high')(example_processing_job)
cache_update_job = job_manager.background_job(queue_name='low')(example_cache_update_job)
long_task = job_manager.background_job(queue_name='default', timeout=120)(example_long_task)