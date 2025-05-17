"""
Startup Cache Module for GloriaMundo Chatbot

This module provides caching functionality to improve application startup performance
by avoiding redundant initializations and operations.
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union

# Setup logging
logger = logging.getLogger(__name__)

class StartupCache:
    """
    Cache manager for tracking and validating initialization operations
    
    This class helps reduce redundant operations during application startup
    by providing mechanisms to track when resources were last initialized
    or updated.
    """
    
    def __init__(self, cache_file: str = '.startup_cache.json'):
        """
        Initialize the startup cache
        
        Args:
            cache_file: Path to the cache file (relative to application root)
        """
        self.cache_file = cache_file
        self.cache_data = self._load_cache()
        
    def _load_cache(self) -> Dict[str, Any]:
        """
        Load the cache from disk if it exists
        
        Returns:
            Dict containing cache data or empty dict if no cache exists
        """
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    logger.debug(f"Loaded startup cache with {len(data)} entries")
                    return data
        except Exception as e:
            logger.warning(f"Error loading startup cache: {e}")
        
        # Return empty cache if file doesn't exist or there was an error
        return {
            'last_updated': datetime.now().isoformat(),
            'services': {}
        }
        
    def _save_cache(self) -> bool:
        """
        Save the cache to disk
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update the last_updated timestamp
            self.cache_data['last_updated'] = datetime.now().isoformat()
            
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_data, f)
            return True
        except Exception as e:
            logger.warning(f"Error saving startup cache: {e}")
            return False
    
    def get_service_data(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data for a specific service
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            Dict containing service data or None if not found
        """
        return self.cache_data.get('services', {}).get(service_name)
    
    def update_service_data(self, service_name: str, data: Dict[str, Any]) -> bool:
        """
        Update the cached data for a service
        
        Args:
            service_name: Name of the service to update
            data: New data to store for the service
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Ensure services dict exists
        if 'services' not in self.cache_data:
            self.cache_data['services'] = {}
            
        # Add timestamp to data
        data['last_updated'] = datetime.now().isoformat()
        
        # Update the service data
        self.cache_data['services'][service_name] = data
        
        # Save to disk
        return self._save_cache()
    
    def service_needs_update(self, service_name: str, max_age_hours: float = 24.0) -> bool:
        """
        Check if a service needs to be updated based on its age
        
        Args:
            service_name: Name of the service to check
            max_age_hours: Maximum age in hours before service should be updated
            
        Returns:
            bool: True if service needs update, False otherwise
        """
        service_data = self.get_service_data(service_name)
        
        # If no data exists, service needs update
        if not service_data:
            return True
            
        # If no timestamp exists, service needs update
        if 'last_updated' not in service_data:
            return True
            
        try:
            # Parse the timestamp
            last_updated = datetime.fromisoformat(service_data['last_updated'])
            
            # Check if it's older than max_age_hours
            age_limit = datetime.now() - timedelta(hours=max_age_hours)
            
            # Service needs update if last_updated is before age_limit
            return last_updated < age_limit
        except Exception as e:
            logger.warning(f"Error checking service age for {service_name}: {e}")
            return True
    
    def clear_cache(self) -> bool:
        """
        Clear the entire cache
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.cache_data = {
            'last_updated': datetime.now().isoformat(),
            'services': {}
        }
        return self._save_cache()

# Create a singleton instance for global use
startup_cache = StartupCache()