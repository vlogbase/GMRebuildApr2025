"""
Jobs Module

This module provides a Redis-backed job system using RQ (Redis Queue) to handle
background processing tasks. It allows for running expensive or long-running
operations asynchronously to improve user experience and application scalability.
"""

import os
import uuid
import time
import logging
import functools
from typing import Dict, List, Optional, Any, Callable, TypeVar, Union, cast
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import RQ
try:
    import redis
    from redis import Redis
    from rq import Queue, Worker, get_current_job, job
    from rq.exceptions import NoSuchJobError
    from rq.job import Job, JobStatus
    JOB_STATUSES = [
        JobStatus.QUEUED, 
        JobStatus.STARTED, 
        JobStatus.FINISHED, 
        JobStatus.FAILED, 
        JobStatus.SCHEDULED, 
        JobStatus.CANCELED
    ]
except ImportError:
    logger.error("RQ not installed. Please install with: pip install rq")
    redis = None
    Queue = None
    Worker = None
    Job = None
    NoSuchJobError = Exception
    JOB_STATUSES = []

# Import Redis helper and config modules
from redis_helper import check_redis_connection, configure_redis
from redis_cache import get_redis_connection

# Type variables
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

# Global Redis connection
_job_redis_connection = None

def get_job_redis_connection():
    """
    Get Redis connection for jobs
    
    Returns:
        Redis connection
    """
    global _job_redis_connection
    
    # Return existing connection if available
    if _job_redis_connection is not None:
        return _job_redis_connection
    
    # Get a new connection
    _job_redis_connection = get_redis_connection()
    return _job_redis_connection

def get_queue(queue_name: str = None) -> Queue:
    """
    Get or create a job queue
    
    Args:
        queue_name: Queue name (optional, default: 'default')
        
    Returns:
        Queue: RQ Queue instance
    """
    # Default queue name
    if queue_name is None:
        queue_name = 'default'
    
    # Check if RQ is available
    if Queue is None:
        class DummyQueue:
            def enqueue(self, *args, **kwargs):
                logger.warning(f"Dummy Queue: Cannot enqueue job in queue '{queue_name}' (RQ not available)")
                return None
            
            def enqueue_at(self, *args, **kwargs):
                logger.warning(f"Dummy Queue: Cannot schedule job in queue '{queue_name}' (RQ not available)")
                return None
            
            def enqueue_in(self, *args, **kwargs):
                logger.warning(f"Dummy Queue: Cannot schedule job in queue '{queue_name}' (RQ not available)")
                return None
            
            def __getattr__(self, name):
                def dummy_method(*args, **kwargs):
                    logger.debug(f"Dummy Queue: {name}() called")
                    return None
                return dummy_method
        
        return DummyQueue()
    
    # Get Redis connection
    redis_conn = get_job_redis_connection()
    if redis_conn is None:
        logger.error("Could not connect to Redis")
        return None
    
    # Create queue
    return Queue(queue_name, connection=redis_conn)

def get_job(job_id: str) -> Optional[Job]:
    """
    Get a job by ID
    
    Args:
        job_id: Job ID
        
    Returns:
        Job: Job instance or None if not found
    """
    # Check if RQ is available
    if Job is None:
        logger.error("RQ not available")
        return None
    
    # Get Redis connection
    redis_conn = get_job_redis_connection()
    if redis_conn is None:
        logger.error("Could not connect to Redis")
        return None
    
    # Get job
    try:
        return Job.fetch(job_id, connection=redis_conn)
    except (NoSuchJobError, Exception) as e:
        logger.error(f"Could not fetch job {job_id}: {e}")
        return None

def get_job_result(job_id: str) -> Any:
    """
    Get job result
    
    Args:
        job_id: Job ID
        
    Returns:
        Any: Job result or None if not available
    """
    job = get_job(job_id)
    if job is None:
        return None
    
    # Check if job is finished
    if job.get_status() != 'finished':
        return None
    
    # Return result
    return job.result

def get_job_status(job_id: str) -> str:
    """
    Get job status
    
    Args:
        job_id: Job ID
        
    Returns:
        str: Job status ('queued', 'started', 'finished', 'failed', 'scheduled', 'canceled', 'unknown')
    """
    job = get_job(job_id)
    if job is None:
        return 'unknown'
    
    return job.get_status()

def get_queue_jobs(queue_name: str = None, status: str = None, count: int = 50) -> List[Dict]:
    """
    Get jobs in a queue
    
    Args:
        queue_name: Queue name (optional, default: 'default')
        status: Filter by status ('queued', 'started', 'finished', 'failed', 'scheduled')
        count: Maximum number of jobs to return
        
    Returns:
        List[Dict]: List of job info dictionaries
    """
    # Default queue name
    if queue_name is None:
        queue_name = 'default'
    
    # Check if RQ is available
    if Queue is None or Job is None:
        logger.error("RQ not available")
        return []
    
    # Get Redis connection
    redis_conn = get_job_redis_connection()
    if redis_conn is None:
        logger.error("Could not connect to Redis")
        return []
    
    # Get registry for status
    queue = Queue(queue_name, connection=redis_conn)
    jobs = []
    
    # Get jobs by status
    if status == 'queued':
        job_ids = queue.get_job_ids()
    elif status == 'started':
        job_ids = Worker.all_worker_job_ids(connection=redis_conn)
    elif status == 'finished':
        job_ids = queue.finished_job_registry.get_job_ids()
    elif status == 'failed':
        job_ids = queue.failed_job_registry.get_job_ids()
    elif status == 'scheduled':
        job_ids = queue.scheduled_job_registry.get_job_ids()
    elif status == 'deferred':
        job_ids = queue.deferred_job_registry.get_job_ids()
    else:
        # Get all jobs
        job_ids = []
        job_ids.extend(queue.get_job_ids())
        job_ids.extend(Worker.all_worker_job_ids(connection=redis_conn) or [])
        job_ids.extend(queue.finished_job_registry.get_job_ids())
        job_ids.extend(queue.failed_job_registry.get_job_ids())
        job_ids.extend(queue.scheduled_job_registry.get_job_ids())
        job_ids.extend(queue.deferred_job_registry.get_job_ids())
    
    # Fetch jobs
    for job_id in job_ids[:count]:
        try:
            job = Job.fetch(job_id, connection=redis_conn)
            jobs.append(get_job_info(job))
        except Exception as e:
            logger.error(f"Error fetching job {job_id}: {e}")
    
    return jobs

def get_job_info(job: Union[Job, str]) -> Dict:
    """
    Get job information
    
    Args:
        job: Job instance or job ID
        
    Returns:
        Dict: Job information
    """
    # Convert job ID to job instance
    if isinstance(job, str):
        job = get_job(job)
    
    if job is None:
        return {'id': 'unknown', 'status': 'unknown'}
    
    # Build job info
    job_info = {
        'id': job.id,
        'queue': job.origin,
        'func_name': job.func_name,
        'args': job.args,
        'kwargs': job.kwargs,
        'result': job.result,
        'status': job.get_status(),
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'enqueued_at': job.enqueued_at.isoformat() if job.enqueued_at else None,
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'ended_at': job.ended_at.isoformat() if job.ended_at else None,
        'meta': job.meta,
        'description': job.description,
    }
    
    # Calculate execution time
    if job.ended_at and job.started_at:
        job_info['execution_time'] = (job.ended_at - job.started_at).total_seconds()
    elif job.started_at:
        job_info['execution_time'] = (datetime.now() - job.started_at).total_seconds()
    else:
        job_info['execution_time'] = None
    
    # Add progress information (if available)
    job_info['progress'] = get_current_job_progress(job)
    
    return job_info

def get_active_workers() -> List[Dict]:
    """
    Get active workers
    
    Returns:
        List[Dict]: List of worker info dictionaries
    """
    # Check if RQ is available
    if Worker is None:
        logger.error("RQ not available")
        return []
    
    # Get Redis connection
    redis_conn = get_job_redis_connection()
    if redis_conn is None:
        logger.error("Could not connect to Redis")
        return []
    
    # Get workers
    workers = Worker.all(connection=redis_conn)
    worker_info = []
    
    for worker in workers:
        info = {
            'name': worker.name,
            'queues': [q.name for q in worker.queues],
            'state': worker.state,
            'current_job': get_job_info(worker.get_current_job_id()) if worker.get_current_job_id() else None,
            'last_heartbeat': worker.last_heartbeat.isoformat() if worker.last_heartbeat else None,
            'birth_date': worker.birth_date.isoformat() if worker.birth_date else None,
            'successful_job_count': worker.successful_job_count,
            'failed_job_count': worker.failed_job_count,
            'total_working_time': worker.total_working_time,
        }
        worker_info.append(info)
    
    return worker_info

def get_queue_counts(queue_name: str = None) -> Dict[str, int]:
    """
    Get job counts for a queue
    
    Args:
        queue_name: Queue name (optional, default: 'default')
        
    Returns:
        Dict[str, int]: Counts by status
    """
    # Default queue name
    if queue_name is None:
        queue_name = 'default'
    
    # Check if RQ is available
    if Queue is None:
        logger.error("RQ not available")
        return {'queued': 0, 'started': 0, 'finished': 0, 'failed': 0, 'scheduled': 0, 'deferred': 0, 'total': 0}
    
    # Get Redis connection
    redis_conn = get_job_redis_connection()
    if redis_conn is None:
        logger.error("Could not connect to Redis")
        return {'queued': 0, 'started': 0, 'finished': 0, 'failed': 0, 'scheduled': 0, 'deferred': 0, 'total': 0}
    
    # Get counts
    queue = Queue(queue_name, connection=redis_conn)
    counts = {
        'queued': queue.count,
        'started': 0,  # Need to count from workers
        'finished': queue.finished_job_registry.count,
        'failed': queue.failed_job_registry.count,
        'scheduled': queue.scheduled_job_registry.count,
        'deferred': queue.deferred_job_registry.count,
    }
    
    # Count jobs in progress from workers
    workers = Worker.all(connection=redis_conn)
    for worker in workers:
        if worker.get_current_job_id() and worker.queue_names_list[0] == queue_name:
            counts['started'] += 1
    
    # Calculate total
    counts['total'] = sum(counts.values())
    
    return counts

def cancel_job(job_id: str) -> bool:
    """
    Cancel a job
    
    Args:
        job_id: Job ID
        
    Returns:
        bool: True if successful
    """
    job = get_job(job_id)
    if job is None:
        return False
    
    # Check if job can be canceled
    status = job.get_status()
    if status in ['finished', 'failed', 'canceled']:
        return False
    
    # Cancel job
    job.cancel()
    job.delete()
    
    return True

def requeue_job(job_id: str) -> bool:
    """
    Requeue a failed job
    
    Args:
        job_id: Job ID
        
    Returns:
        bool: True if successful
    """
    job = get_job(job_id)
    if job is None:
        return False
    
    # Check if job can be requeued
    status = job.get_status()
    if status not in ['failed', 'finished', 'canceled']:
        return False
    
    # Requeue job
    queue = Queue(job.origin, connection=job.connection)
    new_job = queue.enqueue(
        job.func,
        *job.args,
        **job.kwargs,
        description=job.description,
        job_id=str(uuid.uuid4()),
        meta=job.meta
    )
    
    return new_job is not None

def clear_queue(queue_name: str = None) -> bool:
    """
    Clear a queue
    
    Args:
        queue_name: Queue name (optional, default: 'default')
        
    Returns:
        bool: True if successful
    """
    # Default queue name
    if queue_name is None:
        queue_name = 'default'
    
    # Check if RQ is available
    if Queue is None:
        logger.error("RQ not available")
        return False
    
    # Get Redis connection
    redis_conn = get_job_redis_connection()
    if redis_conn is None:
        logger.error("Could not connect to Redis")
        return False
    
    # Clear queue
    queue = Queue(queue_name, connection=redis_conn)
    queue.empty()
    
    # Clear registries
    queue.finished_job_registry.cleanup()
    queue.failed_job_registry.cleanup()
    queue.scheduled_job_registry.cleanup()
    queue.deferred_job_registry.cleanup()
    
    return True

def stop_worker(worker_name: str) -> bool:
    """
    Stop a worker
    
    Args:
        worker_name: Worker name
        
    Returns:
        bool: True if successful
    """
    # Check if RQ is available
    if Worker is None:
        logger.error("RQ not available")
        return False
    
    # Get Redis connection
    redis_conn = get_job_redis_connection()
    if redis_conn is None:
        logger.error("Could not connect to Redis")
        return False
    
    # Find worker
    workers = Worker.all(connection=redis_conn)
    for worker in workers:
        if worker.name == worker_name:
            worker.register_death()
            return True
    
    return False

def log_job_progress(message: str, progress: float = None, status: str = None, result: Any = None, **kwargs):
    """
    Log job progress
    
    Args:
        message: Progress message
        progress: Progress percentage (0-100)
        status: Status message
        result: Partial result
        **kwargs: Additional metadata
    """
    job = get_current_job()
    if job is None:
        logger.debug(f"Progress update (no job): {message}")
        return False
    
    # Update job metadata
    meta = job.meta.copy() if hasattr(job, 'meta') else {}
    
    # Update progress
    if 'progress' not in meta:
        meta['progress'] = {}
    
    now = datetime.now().isoformat()
    meta['progress']['last_update'] = now
    meta['progress']['message'] = message
    
    if progress is not None:
        meta['progress']['percent'] = float(progress)
    
    if status is not None:
        meta['progress']['status'] = status
    
    if result is not None:
        meta['progress']['result'] = result
    
    # Add any additional metadata
    if kwargs:
        for key, value in kwargs.items():
            meta['progress'][key] = value
    
    # Save metadata
    job.meta = meta
    job.save_meta()
    
    return True

def background_job(func=None, *, queue_name=None, timeout=3600, result_ttl=86400, 
                 failure_ttl=86400, ttl=None, description=None, depends_on=None,
                 at_front=False, meta=None, job_id=None):
    """
    Decorator to mark a function as a background job
    
    Args:
        func: Function to decorate
        queue_name: Queue name (default: 'default')
        timeout: Job timeout in seconds (default: 1 hour)
        result_ttl: Result TTL in seconds (default: 1 day)
        failure_ttl: Failure TTL in seconds (default: 1 day)
        ttl: Job TTL in seconds (default: None)
        description: Job description
        depends_on: Job dependency
        at_front: Enqueue at front of queue
        meta: Initial metadata
        job_id: Custom job ID
        
    Returns:
        Decorated function that can be queued
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            """Run the job directly (synchronously)"""
            return f(*args, **kwargs)
        
        def async_run(*args, job_id=None, **kwargs):
            """
            Run the job asynchronously
            
            Args:
                *args: Function arguments
                job_id: Optional job ID (default: auto-generated)
                **kwargs: Function keyword arguments
                
            Returns:
                Job: Job instance
            """
            # Auto-generate job ID if not provided
            if job_id is None:
                job_id = str(uuid.uuid4())
            
            # Get queue
            q = get_queue(queue_name)
            
            # Define metadata
            job_meta = {} if meta is None else meta.copy()
            
            # Add function information to metadata
            job_meta.update({
                'source': f.__module__,
                'function': f.__name__,
                'queue': queue_name or 'default',
                'created_at': datetime.now().isoformat(),
            })
            
            # Enqueue job
            return q.enqueue(
                f,
                *args,
                **kwargs,
                job_id=job_id,
                timeout=timeout,
                result_ttl=result_ttl,
                failure_ttl=failure_ttl,
                ttl=ttl,
                description=description or f.__name__,
                depends_on=depends_on,
                at_front=at_front,
                meta=job_meta
            )
        
        # Attach async_run method to the wrapper
        wrapper.async_run = async_run
        
        # Attach some metadata for introspection
        wrapper._is_job = True
        wrapper._queue_name = queue_name
        wrapper._job_timeout = timeout
        wrapper._job_result_ttl = result_ttl
        
        return wrapper
    
    if func is None:
        return decorator
    
    return decorator(func)

def notify_job_completion(job_id: str, callback_url: str = None, email: str = None) -> bool:
    """
    Set up a notification for when a job completes
    
    Args:
        job_id: Job ID
        callback_url: Callback URL to notify
        email: Email to notify
        
    Returns:
        bool: True if successful
    """
    job = get_job(job_id)
    if job is None:
        return False
    
    # Save notification info in job metadata
    meta = job.meta.copy() if hasattr(job, 'meta') else {}
    
    if 'notifications' not in meta:
        meta['notifications'] = []
    
    # Add notification details
    notification = {'timestamp': datetime.now().isoformat()}
    
    if callback_url:
        notification['type'] = 'webhook'
        notification['url'] = callback_url
    
    if email:
        notification['type'] = 'email'
        notification['address'] = email
    
    meta['notifications'].append(notification)
    
    # Save metadata
    job.meta = meta
    job.save_meta()
    
    return True

def schedule_job(func: Callable, args: List = None, kwargs: Dict = None, 
               queue_name: str = None, job_id: str = None, 
               run_at: datetime = None, run_in: timedelta = None,
               repeat: bool = False, repeat_interval: int = 86400,
               timeout: int = 3600, result_ttl: int = 86400,
               description: str = None, meta: Dict = None) -> Optional[Job]:
    """
    Schedule a job to run later
    
    Args:
        func: Function to run
        args: Function arguments
        kwargs: Function keyword arguments
        queue_name: Queue name
        job_id: Job ID
        run_at: Datetime to run job
        run_in: Timedelta to run job
        repeat: Whether to repeat the job
        repeat_interval: Repeat interval in seconds
        timeout: Job timeout in seconds
        result_ttl: Result TTL in seconds
        description: Job description
        meta: Initial metadata
        
    Returns:
        Job: Scheduled job
    """
    # Check if RQ is available
    if Queue is None:
        logger.error("RQ not available")
        return None
    
    # Validate arguments
    if not callable(func):
        raise ValueError("func must be callable")
    
    if run_at is None and run_in is None:
        raise ValueError("Either run_at or run_in must be provided")
    
    # Calculate time to run
    if run_at is None and run_in is not None:
        run_at = datetime.now() + run_in
    
    # Default arguments
    if args is None:
        args = []
    
    if kwargs is None:
        kwargs = {}
    
    # Auto-generate job ID if not provided
    if job_id is None:
        job_id = str(uuid.uuid4())
    
    # Get queue
    queue = get_queue(queue_name)
    
    # Define metadata
    job_meta = {} if meta is None else meta.copy()
    
    # Add scheduling information to metadata
    job_meta.update({
        'scheduled_at': datetime.now().isoformat(),
        'run_at': run_at.isoformat(),
        'repeat': repeat,
        'repeat_interval': repeat_interval if repeat else None,
    })
    
    # Set default description
    if description is None:
        description = f"Scheduled job: {func.__name__}"
    
    # Schedule job
    try:
        # Handle repeating jobs separately
        if repeat:
            # Schedule first execution
            job = queue.enqueue_at(
                run_at,
                func,
                *args,
                **kwargs,
                job_id=job_id,
                timeout=timeout,
                result_ttl=result_ttl,
                description=description,
                meta=job_meta
            )
            
            # Set up metadata for rescheduling
            job_meta['is_recurring'] = True
            job_meta['next_run'] = (run_at + timedelta(seconds=repeat_interval)).isoformat()
            job.meta = job_meta
            job.save_meta()
            
            return job
        else:
            # Schedule one-time job
            return queue.enqueue_at(
                run_at,
                func,
                *args,
                **kwargs,
                job_id=job_id,
                timeout=timeout,
                result_ttl=result_ttl,
                description=description,
                meta=job_meta
            )
    
    except Exception as e:
        logger.error(f"Error scheduling job: {e}")
        return None

def current_job_progress(message: str = None, progress: float = None, **kwargs):
    """
    Update progress for the current job
    
    Args:
        message: Progress message
        progress: Progress percentage (0-100)
        **kwargs: Additional metadata
    """
    return log_job_progress(message, progress, **kwargs)

def get_current_job_progress(job_or_id: Union[Job, str]) -> Dict:
    """
    Get progress information for a job
    
    Args:
        job_or_id: Job instance or ID
        
    Returns:
        Dict: Progress information
    """
    # Resolve job
    if isinstance(job_or_id, str):
        job = get_job(job_or_id)
    else:
        job = job_or_id
    
    if job is None:
        return {'percent': 0, 'message': 'Unknown job'}
    
    # Get progress from metadata
    meta = job.meta.copy() if hasattr(job, 'meta') and job.meta else {}
    progress_info = meta.get('progress', {})
    
    # Set defaults if not available
    if not progress_info:
        status = job.get_status()
        if status == 'queued':
            progress_info = {'percent': 0, 'message': 'Queued', 'status': 'queued'}
        elif status == 'started':
            progress_info = {'percent': 0, 'message': 'Started', 'status': 'running'}
        elif status == 'finished':
            progress_info = {'percent': 100, 'message': 'Completed', 'status': 'completed'}
        elif status == 'failed':
            progress_info = {'percent': 100, 'message': 'Failed', 'status': 'failed'}
        else:
            progress_info = {'percent': 0, 'message': status.capitalize(), 'status': status}
    
    return progress_info

def wait_for_job(job_id: str, timeout: int = 30, poll_interval: float = 0.5) -> Dict:
    """
    Wait for a job to complete
    
    Args:
        job_id: Job ID
        timeout: Timeout in seconds
        poll_interval: Polling interval in seconds
        
    Returns:
        Dict: Job info
    """
    start_time = time.time()
    job = get_job(job_id)
    
    if job is None:
        return {'status': 'unknown', 'id': job_id, 'error': 'Job not found'}
    
    # Wait for job to complete
    while time.time() - start_time < timeout:
        status = job.get_status()
        
        if status in ['finished', 'failed', 'canceled']:
            break
        
        # Sleep before polling again
        time.sleep(poll_interval)
        
        # Refresh job
        job = get_job(job_id)
        if job is None:
            return {'status': 'unknown', 'id': job_id, 'error': 'Job disappeared'}
    
    # Check for timeout
    if time.time() - start_time >= timeout:
        return {'status': 'timeout', 'id': job_id, 'error': 'Timed out waiting for job'}
    
    # Return full job info
    return get_job_info(job)