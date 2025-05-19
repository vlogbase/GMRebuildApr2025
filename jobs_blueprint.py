"""
Jobs Blueprint Module

This module provides Flask routes for managing background jobs.
It includes a dashboard for viewing and managing job status.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from functools import wraps

from flask import Blueprint, request, render_template, jsonify, redirect, url_for, flash, current_app, g
from rq.job import Job, JobStatus
from rq.exceptions import NoSuchJobError

from jobs import job_manager
from redis_cache import get_redis_connection

# Create blueprint
jobs_bp = Blueprint('jobs', __name__, url_prefix='/jobs', template_folder='templates/jobs')

# Decorator for admin authentication
def admin_required(f):
    """Decorator to restrict access to admin users only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the user is logged in and is an admin
        if not hasattr(g, 'user') or not g.user:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        
        # Check if the user is an admin (specific to your application)
        if not hasattr(g.user, 'is_admin') or not g.user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

# Utility functions
def format_job_for_display(job: Job) -> Dict[str, Any]:
    """
    Format a job for display in templates
    
    Args:
        job (Job): The job to format
        
    Returns:
        dict: Formatted job data
    """
    # Get timestamps as strings
    created_at_str = job.created_at.strftime('%Y-%m-%d %H:%M:%S') if job.created_at else None
    ended_at_str = job.ended_at.strftime('%Y-%m-%d %H:%M:%S') if job.ended_at else None
    enqueued_at_str = job.enqueued_at.strftime('%Y-%m-%d %H:%M:%S') if job.enqueued_at else None
    started_at_str = job.started_at.strftime('%Y-%m-%d %H:%M:%S') if job.started_at else None
    
    # Get the result as a string
    if job.is_finished:
        try:
            result = str(job.result)
        except Exception as e:
            result = f"Error getting result: {str(e)}"
    elif job.is_failed:
        result = f"Job failed: {job.exc_info}"
    elif job.is_started:
        result = "Job is running..."
    else:
        result = "Job has not completed yet"
    
    # Get meta data as a string
    meta = json.dumps(job.meta, indent=2) if job.meta else None
    
    # Format the job data
    job_data = {
        'id': job.id,
        'status': job.get_status(),
        'func_name': job.func_name,
        'description': job.description,
        'origin': job.origin,
        'created_at': job.created_at,
        'created_at_str': created_at_str,
        'enqueued_at': job.enqueued_at,
        'enqueued_at_str': enqueued_at_str,
        'started_at': job.started_at,
        'started_at_str': started_at_str,
        'ended_at': job.ended_at,
        'ended_at_str': ended_at_str,
        'result': result,
        'meta': meta,
        'timeout': job.timeout,
        'ttl': job.ttl,
        'is_failed': job.is_failed,
        'is_finished': job.is_finished,
        'is_queued': job.is_queued,
        'is_started': job.is_started,
        'dependencies': [dep.id for dep in job.dependencies] if job.dependencies else [],
        'progress': job.meta.get('progress', 0) if job.meta else 0
    }
    
    return job_data

# Routes

@jobs_bp.route('/')
@admin_required
def dashboard():
    """Job dashboard showing all queues and jobs"""
    # Get queue statistics
    queue_stats = job_manager.get_queue_stats()
    
    # Get active workers
    workers = job_manager.get_active_workers()
    
    # Get recent jobs
    recent_jobs = []
    for queue_name in job_manager.queues.keys():
        # Get some jobs from each queue
        queue_jobs = job_manager.get_jobs(queue_name, status=None, start=0, end=10)
        for job in queue_jobs:
            recent_jobs.append(format_job_for_display(job))
    
    # Sort recent jobs by creation time
    recent_jobs.sort(key=lambda j: j['created_at'] if j['created_at'] else datetime.min, reverse=True)
    
    # Limit to the 20 most recent jobs
    recent_jobs = recent_jobs[:20]
    
    return render_template(
        'jobs/dashboard.html',
        title='Job Dashboard',
        queue_stats=queue_stats,
        workers=workers,
        recent_jobs=recent_jobs
    )

@jobs_bp.route('/queues/<queue_name>')
@admin_required
def queue_detail(queue_name):
    """Detail view for a specific queue"""
    # Get queue statistics
    queue_stats = job_manager.get_queue_stats(queue_name)
    
    # Get active jobs
    active_jobs = job_manager.get_jobs(queue_name, status='started', start=0, end=100)
    active_jobs = [format_job_for_display(job) for job in active_jobs]
    
    # Get queued jobs
    queued_jobs = job_manager.get_jobs(queue_name, status=None, start=0, end=100)
    queued_jobs = [format_job_for_display(job) for job in queued_jobs]
    
    # Get failed jobs
    failed_jobs = job_manager.get_jobs(queue_name, status='failed', start=0, end=100)
    failed_jobs = [format_job_for_display(job) for job in failed_jobs]
    
    # Get finished jobs
    finished_jobs = job_manager.get_jobs(queue_name, status='finished', start=0, end=100)
    finished_jobs = [format_job_for_display(job) for job in finished_jobs]
    
    # Get scheduled jobs
    scheduled_jobs = job_manager.get_jobs(queue_name, status='scheduled', start=0, end=100)
    scheduled_jobs = [format_job_for_display(job) for job in scheduled_jobs]
    
    return render_template(
        'jobs/queue_detail.html',
        title=f'Queue: {queue_name}',
        queue_stats=queue_stats,
        active_jobs=active_jobs,
        queued_jobs=queued_jobs,
        failed_jobs=failed_jobs,
        finished_jobs=finished_jobs,
        scheduled_jobs=scheduled_jobs
    )

@jobs_bp.route('/jobs/<job_id>')
@admin_required
def job_detail(job_id):
    """Detail view for a specific job"""
    # Fetch the job
    job = job_manager.fetch_job(job_id)
    
    if job is None:
        flash(f'Job {job_id} not found', 'error')
        return redirect(url_for('jobs.dashboard'))
    
    # Format the job
    job_data = format_job_for_display(job)
    
    # Get job arguments
    args_str = None
    kwargs_str = None
    
    try:
        # Get the job's function arguments
        if hasattr(job, 'args') and job.args:
            args_str = json.dumps(job.args, indent=2)
        if hasattr(job, 'kwargs') and job.kwargs:
            kwargs_str = json.dumps(job.kwargs, indent=2)
    except Exception as e:
        args_str = f"Error getting arguments: {str(e)}"
        kwargs_str = None
    
    # Format exception info for display
    exc_info_formatted = None
    if job.exc_info:
        exc_info_formatted = job.exc_info.replace('\n', '<br>')
    
    return render_template(
        'jobs/job_detail.html',
        title=f'Job: {job_id}',
        job=job_data,
        args_str=args_str,
        kwargs_str=kwargs_str,
        exc_info_formatted=exc_info_formatted
    )

@jobs_bp.route('/jobs/<job_id>/cancel', methods=['POST'])
@admin_required
def cancel_job(job_id):
    """Cancel a job"""
    result = job_manager.cancel_job(job_id)
    
    if result:
        flash(f'Job {job_id} has been cancelled', 'success')
    else:
        flash(f'Could not cancel job {job_id}', 'error')
    
    # Check if we should redirect back to a specific page
    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    
    return redirect(url_for('jobs.job_detail', job_id=job_id))

@jobs_bp.route('/jobs/<job_id>/requeue', methods=['POST'])
@admin_required
def requeue_job(job_id):
    """Requeue a failed job"""
    job = job_manager.requeue_job(job_id)
    
    if job:
        flash(f'Job {job_id} has been requeued', 'success')
    else:
        flash(f'Could not requeue job {job_id}', 'error')
    
    # Check if we should redirect back to a specific page
    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    
    return redirect(url_for('jobs.job_detail', job_id=job_id))

@jobs_bp.route('/queues/<queue_name>/clear', methods=['POST'])
@admin_required
def clear_queue(queue_name):
    """Remove all jobs from a queue"""
    result = job_manager.clear_queue(queue_name)
    
    if result:
        flash(f'Queue {queue_name} has been cleared', 'success')
    else:
        flash(f'Could not clear queue {queue_name}', 'error')
    
    return redirect(url_for('jobs.queue_detail', queue_name=queue_name))

@jobs_bp.route('/api/queues')
@admin_required
def api_queues():
    """API endpoint for queue statistics"""
    queue_stats = job_manager.get_queue_stats()
    return jsonify(queue_stats)

@jobs_bp.route('/api/workers')
@admin_required
def api_workers():
    """API endpoint for worker information"""
    workers = job_manager.get_active_workers()
    return jsonify(workers)

@jobs_bp.route('/api/jobs/<job_id>')
@admin_required
def api_job(job_id):
    """API endpoint for job information"""
    job = job_manager.fetch_job(job_id)
    
    if job is None:
        return jsonify({'error': 'Job not found'}), 404
    
    job_data = format_job_for_display(job)
    return jsonify(job_data)

@jobs_bp.route('/api/jobs/<job_id>/progress')
@admin_required
def api_job_progress(job_id):
    """API endpoint for job progress"""
    job = job_manager.fetch_job(job_id)
    
    if job is None:
        return jsonify({'error': 'Job not found'}), 404
    
    progress = job.meta.get('progress', 0) if job.meta else 0
    status = job.get_status()
    
    return jsonify({
        'id': job.id,
        'status': status,
        'progress': progress,
        'complete': status in ('finished', 'failed'),
        'failed': status == 'failed'
    })

def init_app(app):
    """Register blueprint with app"""
    app.register_blueprint(jobs_bp)
    
    # Add job manager to app context
    app.job_manager = job_manager