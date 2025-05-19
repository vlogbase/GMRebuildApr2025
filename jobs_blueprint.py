"""
Jobs Blueprint Module for GloriaMundo Chatbot

This module provides routes for managing and monitoring background jobs.
It integrates with Redis Queue (RQ) for job processing.
"""

import os
import json
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for, current_app
from flask_login import login_required, current_user
from rq import Queue, Worker
from rq.job import Job
from rq.exceptions import NoSuchJobError
from rq.registry import FinishedJobRegistry, FailedJobRegistry, StartedJobRegistry
from redis_cache import redis_cache
from jobs import queues

logger = logging.getLogger(__name__)

# Create the Blueprint
jobs_bp = Blueprint('jobs', __name__, template_folder='templates')

@jobs_bp.route('/')
@login_required
def index():
    """
    Display the jobs dashboard
    """
    # Verify that user is an admin
    if not is_admin():
        abort(403, "Access denied: Admin privileges required")
    
    # Get all queues and stats
    stats = {
        'queues': list(queues.keys()),
        'queued_jobs': 0,
        'active_workers': 0,
        'workers': [],
        'finished_jobs': 0,
        'failed_jobs': 0
    }
    
    queue_stats = []
    for name, queue in queues.items():
        finished_registry = FinishedJobRegistry(queue=queue)
        failed_registry = FailedJobRegistry(queue=queue)
        started_registry = StartedJobRegistry(queue=queue)
        
        queue_info = {
            'name': name,
            'count': queue.count,
            'active_count': len(started_registry),
            'finished_count': len(finished_registry),
            'failed_count': len(failed_registry)
        }
        queue_stats.append(queue_info)
        
        # Update total stats
        stats['queued_jobs'] += queue.count
        stats['finished_jobs'] += len(finished_registry)
        stats['failed_jobs'] += len(failed_registry)
    
    # Get worker information
    workers = Worker.all(connection=redis_cache.get_redis())
    worker_info = []
    for worker in workers:
        # Get the current job for this worker, if any
        current_job = worker.get_current_job()
        worker_data = {
            'name': worker.name,
            'pid': getattr(worker, 'pid', 'N/A'),
            'queues': worker.queues,
            'state': 'busy' if current_job else 'idle',
            'current_job': current_job,
            'birth_date': worker.birth_date.strftime('%Y-%m-%d %H:%M:%S') if hasattr(worker, 'birth_date') else 'N/A'
        }
        worker_info.append(worker_data)
    
    stats['workers'] = worker_info
    stats['active_workers'] = len([w for w in worker_info if w['state'] == 'busy'])
    
    return render_template('jobs/dashboard.html', 
                           queues=queue_stats, 
                           workers=worker_info, 
                           stats=stats)

@jobs_bp.route('/queue/<queue_name>')
@jobs_bp.route('/queue/<queue_name>/<status>')
@login_required
def view_queue(queue_name, status='all'):
    """
    View jobs in a specific queue with optional status filtering
    
    Args:
        queue_name (str): Name of the queue to view
        status (str, optional): Status filter ('all', 'queued', 'active', 'finished', 'failed')
    """
    if not is_admin():
        abort(403, "Access denied: Admin privileges required")
    
    if queue_name not in queues:
        abort(404, f"Queue '{queue_name}' not found")
    
    queue = queues[queue_name]
    
    # Pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Get jobs based on status
    jobs = []
    
    try:
        if status == 'queued' or status == 'all':
            # Get all job IDs then apply pagination
            all_job_ids = queue.job_ids
            job_ids = all_job_ids[(page-1)*per_page:page*per_page]
            for job_id in job_ids:
                try:
                    job = Job.fetch(job_id, connection=redis_cache.get_redis())
                    jobs.append({
                        'id': job.id,
                        'status': 'queued',
                        'created_at': job.created_at.strftime('%Y-%m-%d %H:%M:%S') if job.created_at else 'N/A',
                        'description': job.description
                    })
                except NoSuchJobError:
                    continue
    
        if status == 'active' or status == 'all':
            registry = StartedJobRegistry(queue=queue)
            job_ids = registry.get_job_ids()
            for job_id in job_ids:
                try:
                    job = Job.fetch(job_id, connection=redis_cache.get_redis())
                    jobs.append({
                        'id': job.id,
                        'status': 'active',
                        'created_at': job.created_at.strftime('%Y-%m-%d %H:%M:%S') if job.created_at else 'N/A',
                        'description': job.description
                    })
                except NoSuchJobError:
                    continue
    
        if status == 'finished' or status == 'all':
            registry = FinishedJobRegistry(queue=queue)
            job_ids = registry.get_job_ids()
            for job_id in job_ids:
                try:
                    job = Job.fetch(job_id, connection=redis_cache.get_redis())
                    jobs.append({
                        'id': job.id,
                        'status': 'finished',
                        'created_at': job.created_at.strftime('%Y-%m-%d %H:%M:%S') if job.created_at else 'N/A',
                        'description': job.description
                    })
                except NoSuchJobError:
                    continue
    
        if status == 'failed' or status == 'all':
            registry = FailedJobRegistry(queue=queue)
            job_ids = registry.get_job_ids()
            for job_id in job_ids:
                try:
                    job = Job.fetch(job_id, connection=redis_cache.get_redis())
                    jobs.append({
                        'id': job.id,
                        'status': 'failed',
                        'created_at': job.created_at.strftime('%Y-%m-%d %H:%M:%S') if job.created_at else 'N/A',
                        'description': job.description
                    })
                except NoSuchJobError:
                    continue
                    
    except Exception as e:
        logger.error(f"Error fetching jobs for queue {queue_name}: {str(e)}")
        abort(500, f"Error fetching jobs: {str(e)}")
        
    return render_template('jobs/queue.html', 
                           queue_name=queue_name, 
                           job_status=status, 
                           jobs=jobs, 
                           page=page, 
                           per_page=per_page)

@jobs_bp.route('/job/<job_id>')
@login_required
def view_job(job_id):
    """
    View details of a specific job
    
    Args:
        job_id (str): ID of the job to view
    """
    if not is_admin():
        abort(403, "Access denied: Admin privileges required")
    
    try:
        job = Job.fetch(job_id, connection=redis_cache.get_redis())
        
        # Format data for display
        created_at_str = job.created_at.strftime('%Y-%m-%d %H:%M:%S') if job.created_at else 'N/A'
        ended_at_str = job.ended_at.strftime('%Y-%m-%d %H:%M:%S') if job.ended_at else 'N/A'
        enqueued_at_str = job.enqueued_at.strftime('%Y-%m-%d %H:%M:%S') if job.enqueued_at else 'N/A'
        started_at_str = job.started_at.strftime('%Y-%m-%d %H:%M:%S') if job.started_at else 'N/A'
        
        # Add the formatted dates as new attributes to avoid trying to modify Job properties
        job.created_at_str = created_at_str
        job.ended_at_str = ended_at_str
        job.enqueued_at_str = enqueued_at_str
        job.started_at_str = started_at_str
            
        # Format result and args/kwargs for display
        if job.result:
            try:
                if isinstance(job.result, (dict, list)):
                    job.result = json.dumps(job.result, indent=2)
                else:
                    job.result = str(job.result)
            except:
                job.result = str(job.result)
        
        # Format args and kwargs
        job.args = ', '.join([str(arg) for arg in job.args]) if job.args else ''
        
        if job.kwargs:
            formatted_kwargs = []
            for key, value in job.kwargs.items():
                if isinstance(value, (dict, list)):
                    formatted_value = json.dumps(value)
                else:
                    formatted_value = str(value)
                formatted_kwargs.append(f"{key}={formatted_value}")
            job.kwargs = ', '.join(formatted_kwargs)
            
        # Format meta data
        if job.meta:
            job.meta = json.dumps(job.meta, indent=2)
            
        return render_template('jobs/job_detail.html', job=job)
        
    except NoSuchJobError:
        abort(404, f"Job {job_id} not found")
    except Exception as e:
        logger.error(f"Error fetching job {job_id}: {str(e)}")
        abort(500, f"Error fetching job: {str(e)}")

@jobs_bp.route('/job/<job_id>/requeue', methods=['POST'])
@login_required
def requeue_job(job_id):
    """
    Requeue a failed job
    
    Args:
        job_id (str): ID of the job to requeue
    """
    if not is_admin():
        abort(403, "Access denied: Admin privileges required")
    
    try:
        job = Job.fetch(job_id, connection=redis_cache.get_redis())
        
        # Get the original queue
        queue = queues.get(job.origin) or queues['default']
        
        # Requeue the job
        new_job = queue.enqueue_job(job)
        
        return redirect(url_for('jobs.view_job', job_id=new_job.id))
        
    except NoSuchJobError:
        abort(404, f"Job {job_id} not found")
    except Exception as e:
        logger.error(f"Error requeuing job {job_id}: {str(e)}")
        abort(500, f"Error requeuing job: {str(e)}")

@jobs_bp.route('/job/<job_id>/delete', methods=['POST'])
@login_required
def delete_job(job_id):
    """
    Delete a job from the queue and registry
    
    Args:
        job_id (str): ID of the job to delete
    """
    if not is_admin():
        abort(403, "Access denied: Admin privileges required")
    
    try:
        job = Job.fetch(job_id, connection=redis_cache.get_redis())
        queue_name = job.origin
        
        # Delete the job
        job.delete()
        
        return redirect(url_for('jobs.view_queue', queue_name=queue_name))
        
    except NoSuchJobError:
        abort(404, f"Job {job_id} not found")
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        abort(500, f"Error deleting job: {str(e)}")

@jobs_bp.route('/queue/<queue_name>/empty', methods=['POST'])
@login_required
def empty_queue(queue_name):
    """
    Empty all jobs from a queue
    
    Args:
        queue_name (str): Name of the queue to empty
    """
    if not is_admin():
        abort(403, "Access denied: Admin privileges required")
    
    if queue_name not in queues:
        abort(404, f"Queue '{queue_name}' not found")
    
    try:
        queue = queues[queue_name]
        
        # Empty the queue
        queue.empty()
        
        return redirect(url_for('jobs.view_queue', queue_name=queue_name))
        
    except Exception as e:
        logger.error(f"Error emptying queue {queue_name}: {str(e)}")
        abort(500, f"Error emptying queue: {str(e)}")

@jobs_bp.route('/enqueue-test-job', methods=['GET', 'POST'])
@login_required
def enqueue_test_job():
    """
    Enqueue a test job for demonstration purposes
    """
    if not is_admin():
        abort(403, "Access denied: Admin privileges required")
    
    try:
        # Default to export job type
        job_type = request.form.get('job_type', 'export')
        queue_name = request.form.get('queue', 'default')
        description = request.form.get('description', 'Test job')
        
        queue = queues.get(queue_name) or queues['default']
        
        # Import our job functions from jobs.py
        from jobs import export_user_data, process_large_document, send_batch_notifications, calculate_usage_statistics
        
        # Enqueue the appropriate job based on type
        if job_type == 'export':
            job = queue.enqueue(
                export_user_data,
                user_id=123,
                description=description or 'Export user data test job'
            )
        elif job_type == 'document':
            job = queue.enqueue(
                process_large_document,
                document_id='test-doc-123',
                options={'summary_length': 'medium'},
                description=description or 'Document processing test job'
            )
        elif job_type == 'notifications':
            job = queue.enqueue(
                send_batch_notifications,
                user_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                notification_type='email',
                message='This is a test notification',
                description=description or 'Batch notifications test job'
            )
        elif job_type == 'stats':
            job = queue.enqueue(
                calculate_usage_statistics,
                start_date='2023-01-01',
                end_date=datetime.now().strftime('%Y-%m-%d'),
                description=description or 'Usage statistics calculation test job'
            )
        else:
            abort(400, f"Invalid job type: {job_type}")
        
        # Add flash message for better user feedback
        if job:
            flash(f'Test job of type "{job_type}" enqueued successfully with ID: {job.id}', 'success')
        
        return redirect(url_for('jobs.view_job', job_id=job.id))
        
    except Exception as e:
        logger.error(f"Error enqueueing test job: {str(e)}")
        abort(500, f"Error enqueueing test job: {str(e)}")

def is_admin():
    """Check if the current user is an admin"""
    if hasattr(current_user, 'email'):
        return current_user.email == 'andy@sentigral.com'
    return False

def init_app(app):
    """
    Initialize the jobs blueprint with the Flask app
    
    Args:
        app (Flask): The Flask application instance
    """
    app.register_blueprint(jobs_bp, url_prefix='/jobs')
    logger.info("Jobs blueprint registered with prefix /jobs")