"""
Background Initializer Module

This module centralizes and manages background initialization tasks to improve application
startup performance by deferring non-critical operations.
"""

import threading
import time
import logging
from typing import Dict, List, Any, Callable, Optional, TypedDict, Union, cast
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

# Define TypedDict for task results
class TaskResult(TypedDict, total=False):
    """Type definition for task results"""
    success: bool
    result: Optional[Any]
    error: Optional[str]
    time: float
    completed_at: str

class BackgroundInitializer:
    """
    Manages deferred initialization of services and resources to optimize application startup
    
    This class prioritizes initialization tasks and runs them in order of priority,
    with optional dependencies between tasks.
    """
    
    def __init__(self):
        """Initialize the background initializer with empty task lists"""
        self.tasks = {}  # Dictionary of tasks: name -> task definition
        self.results = {}  # Dictionary of task results: name -> result
        self.started = False
        self.thread = None
        
    def add_task(self, name: str, func: Callable, priority: int = 1, 
                dependencies: Optional[List[str]] = None, timeout: int = 60):
        """
        Add a task to be executed in the background
        
        Args:
            name: Unique name for the task
            func: Function to execute
            priority: Priority level (lower numbers run first)
            dependencies: List of task names that must complete before this one runs
            timeout: Maximum seconds to allow for task execution
        """
        actual_dependencies: List[str] = [] if dependencies is None else dependencies
            
        self.tasks[name] = {
            'name': name,
            'func': func,
            'priority': priority,
            'dependencies': dependencies,
            'timeout': timeout,
            'status': 'pending'
        }
        logger.debug(f"Added background task: {name} (priority: {priority}, dependencies: {dependencies})")
        
    def _task_wrapper(self, task):
        """Wrap task execution with error handling and timing"""
        task_name = task['name']
        timeout = task.get('timeout', 60)
        
        # Update status
        task['status'] = 'running'
        
        start_time = time.time()
        logger.info(f"Starting background task: {task_name} (timeout: {timeout}s)")
        
        try:
            # Execute the task with timeout protection
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Task {task_name} timed out after {timeout} seconds")
            
            # Set up timeout signal (only on Unix systems)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout)
            
            try:
                result = task['func']()
                success = True
                error = None
            finally:
                # Clear the alarm
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                    
        except TimeoutError as e:
            logger.error(f"Background task {task_name} timed out: {e}")
            result = None
            success = False
            error = str(e)
        except Exception as e:
            logger.error(f"Error in background task {task_name}: {e}", exc_info=True)
            result = None
            success = False
            error = str(e)
            
        elapsed_time = time.time() - start_time
        logger.info(f"Completed background task: {task_name} in {elapsed_time:.2f}s (success: {success})")
        
        # Store the result
        task['status'] = 'completed' if success else 'failed'
        self.results[task_name] = {
            'success': success,
            'result': result if success else None,
            'error': error,
            'time': elapsed_time,
            'completed_at': datetime.now().isoformat()
        }
        
    def _can_run_task(self, task):
        """Check if a task's dependencies have been met"""
        # Safely handle dependencies that might be None
        dependencies = task.get('dependencies', [])
        if dependencies is None:
            dependencies = []
            
        for dep_name in dependencies:
            # The dependency must exist and be completed successfully
            if dep_name not in self.results:
                return False
                
            if not self.results[dep_name]['success']:
                logger.warning(f"Task {task['name']} dependency {dep_name} failed, skipping")
                return False
                
        return True
    
    def _run_tasks_in_order(self):
        """Run all tasks in order of priority, respecting dependencies"""
        # Sort tasks by priority
        sorted_tasks = sorted(self.tasks.values(), key=lambda t: t['priority'])
        
        while sorted_tasks:
            # Find tasks that can be run (all dependencies satisfied)
            runnable_tasks = [t for t in sorted_tasks if self._can_run_task(t)]
            
            if not runnable_tasks:
                # If we have tasks but none can run, we have a dependency cycle
                remaining = [t['name'] for t in sorted_tasks]
                logger.error(f"Unable to run remaining tasks due to dependency issues: {remaining}")
                break
                
            # Run the first runnable task
            task = runnable_tasks[0]
            self._task_wrapper(task)
            
            # Remove the task from the list
            sorted_tasks = [t for t in sorted_tasks if t['name'] != task['name']]
    
    def start(self):
        """Start the background initialization process in a separate thread"""
        if self.started:
            logger.warning("Background initializer already started")
            return
            
        self.started = True
        
        # Create and start the thread
        self.thread = threading.Thread(
            target=self._run_tasks_in_order, 
            daemon=True,
            name="background-initializer"
        )
        self.thread.start()
        
        logger.info(f"Started background initializer with {len(self.tasks)} tasks")
    
    def get_result(self, task_name: str) -> TaskResult:
        """
        Get the result of a completed task
        
        Returns:
            Dictionary with 'success', 'result'/'error', and 'time' keys
        """
        if task_name not in self.results:
            return cast(TaskResult, {'success': False, 'error': 'Task not found or not completed yet'})
            
        return self.results[task_name]
    
    def all_completed(self) -> bool:
        """Check if all tasks have completed"""
        if not self.tasks:
            return True
            
        return len(self.results) == len(self.tasks)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of all task statuses"""
        summary = {
            'tasks_total': len(self.tasks),
            'tasks_completed': len(self.results),
            'tasks_successful': sum(1 for r in self.results.values() if r['success']),
            'tasks_failed': sum(1 for r in self.results.values() if not r['success']),
            'tasks_pending': len(self.tasks) - len(self.results),
            'task_details': {}
        }
        
        # Add details for each task
        for name, task in self.tasks.items():
            if name in self.results:
                result = self.results[name]
                status = 'completed' if result['success'] else 'failed'
                time_taken = result['time']
                error = result.get('error', None)
            else:
                status = task['status']
                time_taken = None
                error = None
                
            summary['task_details'][name] = {
                'status': status,
                'priority': task['priority'],
                'dependencies': task['dependencies'],
                'time_taken': time_taken,
                'error': error
            }
            
        return summary