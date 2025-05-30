"""
Jobs Blueprint Module (Improved)

This module provides a Flask blueprint for the job management web interface.
This implementation resolves circular import issues and prevents the blueprint 
from being registered multiple times.
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app, flash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
jobs_bp = Blueprint('jobs', __name__, url_prefix='/jobs', template_folder='templates')

# Job status CSS classes for templates
JOB_STATUS_CLASSES = {
    'queued': 'bg-blue-100 text-blue-800',
    'started': 'bg-yellow-100 text-yellow-800',
    'deferred': 'bg-purple-100 text-purple-800',
    'finished': 'bg-green-100 text-green-800',
    'failed': 'bg-red-100 text-red-800',
    'scheduled': 'bg-indigo-100 text-indigo-800',
    'canceled': 'bg-gray-100 text-gray-800',
    'unknown': 'bg-gray-100 text-gray-800'
}

# Define all routes before the blueprint is registered
@jobs_bp.route('/')
def dashboard():
    """Job dashboard view"""
    # Import job functions here to avoid circular imports
    from jobs import get_queue_counts, get_active_workers, get_queue_jobs
    
    # Get active queues
    queues = ['high', 'default', 'low', 'email', 'indexing']
    
    # Get job counts for each queue
    queue_stats = {}
    for queue_name in queues:
        queue_stats[queue_name] = get_queue_counts(queue_name)
    
    # Get active workers
    workers = get_active_workers()
    
    # Get recent jobs (across all queues)
    recent_jobs = []
    for queue_name in queues:
        # Handle None status safely
        jobs = get_queue_jobs(queue_name, status=None, count=10)
        if jobs:
            recent_jobs.extend(jobs)
    
    # Sort by enqueued time (newest first)
    recent_jobs.sort(key=lambda job: job.get('enqueued_at', ''), reverse=True)
    recent_jobs = recent_jobs[:20]  # Limit to 20 jobs
    
    return render_template(
        'jobs/dashboard.html',
        queues=queues,
        queue_stats=queue_stats,
        workers=workers,
        recent_jobs=recent_jobs
    )

@jobs_bp.route('/queue/<queue_name>')
def queue_detail(queue_name):
    """Queue detail view"""
    # Import job functions here to avoid circular imports
    from jobs import get_queue_jobs, get_queue_counts
    
    # Get status filter (if any)
    status = request.args.get('status')
    
    # Get page number
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    
    # Get jobs for the queue - handle None status safely
    jobs = get_queue_jobs(queue_name, status=status, count=100) or []
    
    # Get queue stats
    stats = get_queue_counts(queue_name)
    
    # Add timestamp
    now = datetime.now().isoformat()
    
    return render_template(
        'jobs/queue_detail.html',
        queue_name=queue_name,
        stats=stats,
        jobs=jobs,
        status=status,
        page=page,
        timestamp=now
    )

@jobs_bp.route('/job/<job_id>')
def job_detail(job_id):
    """Job detail view"""
    # Import job functions here to avoid circular imports
    from jobs import get_job_info
    
    # Get job
    job_info = get_job_info(job_id)
    
    if not job_info or job_info.get('id') == 'unknown':
        flash('Job not found', 'error')
        return redirect(url_for('jobs.dashboard'))
    
    # Get timestamp
    now = datetime.now().isoformat()
    
    return render_template(
        'jobs/job_detail.html',
        job=job_info,
        timestamp=now
    )

# API routes
@jobs_bp.route('/api/queues')
def api_list_queues():
    """API: List queues"""
    # Import job functions here to avoid circular imports
    from jobs import get_queue_counts
    
    queues = ['high', 'default', 'low', 'email', 'indexing']
    result = []
    
    for queue_name in queues:
        stats = get_queue_counts(queue_name)
        queue_info = {
            'name': queue_name,
            'stats': stats
        }
        result.append(queue_info)
    
    return jsonify({
        'queues': result,
        'timestamp': datetime.now().isoformat()
    })

@jobs_bp.route('/api/workers')
def api_list_workers():
    """API: List workers"""
    # Import job functions here to avoid circular imports
    from jobs import get_active_workers
    
    workers = get_active_workers()
    
    return jsonify({
        'workers': workers,
        'count': len(workers),
        'timestamp': datetime.now().isoformat()
    })

@jobs_bp.route('/api/jobs/<queue_name>')
def api_list_jobs(queue_name):
    """API: List jobs in a queue"""
    # Import job functions here to avoid circular imports
    from jobs import get_queue_jobs
    
    # Get status filter (if any)
    status = request.args.get('status')
    
    # Get jobs - handle None status safely
    jobs = get_queue_jobs(queue_name, status=status, count=50) or []
    
    return jsonify({
        'queue': queue_name,
        'status': status,
        'jobs': jobs,
        'count': len(jobs),
        'timestamp': datetime.now().isoformat()
    })

@jobs_bp.route('/api/job/<job_id>')
def api_job_detail(job_id):
    """API: Get job details"""
    # Import job functions here to avoid circular imports
    from jobs import get_job_info
    
    job_info = get_job_info(job_id)
    
    return jsonify({
        'job': job_info,
        'timestamp': datetime.now().isoformat()
    })

@jobs_bp.route('/api/job/<job_id>/cancel', methods=['POST'])
def api_cancel_job(job_id):
    """API: Cancel a job"""
    # Import job functions here to avoid circular imports
    from jobs import cancel_job
    
    result = cancel_job(job_id)
    
    return jsonify({
        'job_id': job_id,
        'action': 'cancel',
        'success': result,
        'timestamp': datetime.now().isoformat()
    })

@jobs_bp.route('/api/job/<job_id>/requeue', methods=['POST'])
def api_requeue_job(job_id):
    """API: Requeue a failed job"""
    # Import job functions here to avoid circular imports
    from jobs import requeue_job
    
    result = requeue_job(job_id)
    
    return jsonify({
        'job_id': job_id,
        'action': 'requeue',
        'success': result,
        'timestamp': datetime.now().isoformat()
    })

@jobs_bp.route('/api/queue/<queue_name>/clear', methods=['POST'])
def api_clear_queue(queue_name):
    """API: Clear a queue"""
    # Import job functions here to avoid circular imports
    from jobs import clear_queue
    
    result = clear_queue(queue_name)
    
    return jsonify({
        'queue': queue_name,
        'action': 'clear',
        'success': result,
        'timestamp': datetime.now().isoformat()
    })

# Web action routes (non-API)
@jobs_bp.route('/action/job/<job_id>/cancel', methods=['POST'])
def action_cancel_job(job_id):
    """Web action: Cancel a job"""
    # Import job functions here to avoid circular imports
    from jobs import cancel_job
    
    result = cancel_job(job_id)
    
    if result:
        flash(f'Job {job_id} has been canceled', 'success')
    else:
        flash(f'Failed to cancel job {job_id}', 'error')
    
    # Redirect back to job detail or referer
    if request.referrer:
        return redirect(request.referrer)
    else:
        return redirect(url_for('jobs.job_detail', job_id=job_id))

@jobs_bp.route('/action/job/<job_id>/requeue', methods=['POST'])
def action_requeue_job(job_id):
    """Web action: Requeue a failed job"""
    # Import job functions here to avoid circular imports
    from jobs import requeue_job
    
    result = requeue_job(job_id)
    
    if result:
        flash(f'Job {job_id} has been requeued', 'success')
    else:
        flash(f'Failed to requeue job {job_id}', 'error')
    
    # Redirect back to job detail or referer
    if request.referrer:
        return redirect(request.referrer)
    else:
        return redirect(url_for('jobs.job_detail', job_id=job_id))

@jobs_bp.route('/action/queue/<queue_name>/clear', methods=['POST'])
def action_clear_queue(queue_name):
    """Web action: Clear a queue"""
    # Import job functions here to avoid circular imports
    from jobs import clear_queue
    
    result = clear_queue(queue_name)
    
    if result:
        flash(f'Queue {queue_name} has been cleared', 'success')
    else:
        flash(f'Failed to clear queue {queue_name}', 'error')
    
    # Redirect back to queue detail or referer
    if request.referrer:
        return redirect(request.referrer)
    else:
        return redirect(url_for('jobs.queue_detail', queue_name=queue_name))

# Define job status helper function for templates
def job_status_classes():
    """Provide job status CSS classes to templates"""
    return {'job_status_classes': JOB_STATUS_CLASSES}

def init_app(app):
    """
    Initialize the jobs blueprint with a Flask application
    
    This function registers the jobs blueprint and adds its context processors.
    It carefully avoids circular imports and re-registration issues.
    
    Args:
        app: Flask application
        
    Returns:
        None
    """
    try:
        # Register the context processor first
        app.context_processor(job_status_classes)
        
        # Then register the blueprint
        app.register_blueprint(jobs_bp)
        
        logger.info("Jobs blueprint initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing jobs blueprint: {e}")