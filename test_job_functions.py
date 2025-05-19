"""
Test Job Functions

This module contains example job functions that can be used to test the background job system.
These functions are imported by jobs_blueprint.py and used for testing queuing and execution.
"""

import time
import random
import logging
import os
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def example_job(message="Hello, World!"):
    """
    Example job function that simply returns a message.
    
    Args:
        message (str): The message to return
        
    Returns:
        dict: A dictionary containing the result of the job
    """
    job_id = random.randint(1000, 9999)
    logger.info(f"Running example job #{job_id} with message: {message}")
    
    # Add a small delay to simulate work
    time.sleep(1)
    
    # Return the result
    result = {
        "job_id": job_id,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("FLASK_ENV", "unknown")
    }
    
    logger.info(f"Job #{job_id} completed successfully: {result}")
    return result

def example_long_job(duration=10, steps=5):
    """
    Example job function that runs for a longer duration, reporting progress along the way.
    
    Args:
        duration (int): The total duration in seconds
        steps (int): The number of steps to break the job into
        
    Returns:
        dict: A dictionary containing the result of the job
    """
    job_id = random.randint(1000, 9999)
    logger.info(f"Running long job #{job_id} with duration: {duration}s and {steps} steps")
    
    # Calculate time per step
    step_time = duration / steps
    
    # Process each step
    results = []
    for step in range(1, steps + 1):
        # Simulate work for this step
        time.sleep(step_time)
        
        # Log progress
        progress = (step / steps) * 100
        logger.info(f"Job #{job_id} - Step {step}/{steps} completed ({progress:.1f}%)")
        
        # Save step result
        step_result = {
            "step": step,
            "progress": f"{progress:.1f}%",
            "timestamp": datetime.now().isoformat()
        }
        results.append(step_result)
    
    # Return the final result
    result = {
        "job_id": job_id,
        "total_duration": duration,
        "steps_completed": steps,
        "step_results": results,
        "completed_at": datetime.now().isoformat()
    }
    
    logger.info(f"Long job #{job_id} completed successfully")
    return result

def example_failing_job(fail_type="exception"):
    """
    Example job function that intentionally fails to test error handling.
    
    Args:
        fail_type (str): The type of failure to simulate
            - "exception": Raise an exception
            - "timeout": Run indefinitely (to trigger timeout)
            - "invalid_return": Return an invalid object
            
    Returns:
        None: This job is expected to fail
    """
    job_id = random.randint(1000, 9999)
    logger.info(f"Running failing job #{job_id} with fail_type: {fail_type}")
    
    if fail_type == "exception":
        # Simulate an exception
        logger.info(f"Job #{job_id} about to raise an exception")
        raise ValueError(f"Intentional exception from job #{job_id} for testing")
        
    elif fail_type == "timeout":
        # Simulate a timeout by sleeping for a very long time
        logger.info(f"Job #{job_id} about to hang indefinitely (timeout)")
        time.sleep(3600)  # Sleep for an hour (should timeout before this)
        
    elif fail_type == "invalid_return":
        # Return something that can't be pickled/serialized
        logger.info(f"Job #{job_id} about to return an invalid result")
        
        # Create a circular reference
        a = {}
        b = {}
        a["b"] = b
        b["a"] = a
        
        return a
    
    else:
        # Unknown failure type
        raise ValueError(f"Unknown fail_type: {fail_type}")