"""
Redis Cache Module

This module provides a Redis connection manager for use with caching, session storage,
and background job processing. It handles SSL connections to Azure Redis Cache.
"""

import os
import json
import logging
import redis
from typing import Any, Dict, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def get_redis_connection(decode_responses=False):
    """
    Get a connection to Redis using SSL for Azure Redis Cache
    
    Args:
        decode_responses (bool): Whether to decode responses from Redis as strings
        
    Returns:
        Redis: A Redis connection object
    """
    # Get Redis configuration from environment variables
    redis_host = os.environ.get("REDIS_HOST", "my-bullmq-cache.redis.cache.windows.net")
    redis_port = int(os.environ.get("REDIS_PORT", 6380))
    redis_password = os.environ.get("REDIS_PASSWORD", "")
    
    # Check required configuration
    if not redis_password:
        raise ValueError("Redis password is required but not provided in environment variables")
    
    # Log connection attempt (without sensitive info)
    logger.info(f"Connecting to Redis at {redis_host}:{redis_port} with SSL")
    
    try:
        # Create Redis client with SSL
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            ssl=True,
            ssl_cert_reqs="none",  # Disable certificate validation for simplicity
            decode_responses=decode_responses,
            socket_timeout=10,
            socket_connect_timeout=10,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        
        # Test connection
        redis_client.ping()
        logger.info("Successfully connected to Redis")
        
        return redis_client
    except redis.RedisError as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        raise

class RedisCache:
    """
    A Redis-based cache implementation
    
    This class provides a simple interface for caching data in Redis.
    It handles serialization and deserialization of data.
    """
    
    def __init__(self, namespace='general', expire_time=3600):
        """
        Initialize the Redis cache
        
        Args:
            namespace (str): The namespace to use for keys
            expire_time (int): The default expiration time in seconds
        """
        self.namespace = namespace
        self.expire_time = expire_time
        self._redis = None
        self._connect()
    
    def _connect(self):
        """Establish the Redis connection"""
        if self._redis is None:
            try:
                self._redis = get_redis_connection()
            except Exception as e:
                logger.error(f"Failed to initialize Redis cache: {str(e)}")
                raise
    
    def _make_key(self, key):
        """
        Create a namespaced key
        
        Args:
            key (str): The original key
            
        Returns:
            str: The namespaced key
        """
        return f"{self.namespace}:{key}"
    
    def get(self, key, default=None):
        """
        Get a value from the cache
        
        Args:
            key (str): The key to get
            default: The default value to return if the key doesn't exist
            
        Returns:
            The cached value, or the default
        """
        try:
            self._connect()
            value = self._redis.get(self._make_key(key))
            if value is None:
                return default
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # If not JSON, return the raw value
                return value
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {str(e)}")
            return default
    
    def set(self, key, value, expire=None):
        """
        Set a value in the cache
        
        Args:
            key (str): The key to set
            value: The value to cache
            expire (int, optional): Override the default expiration time
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._connect()
            # Serialize non-string values to JSON
            if not isinstance(value, (str, bytes, bytearray)):
                value = json.dumps(value)
            
            # Set with expiration
            expiration = expire if expire is not None else self.expire_time
            return self._redis.setex(
                self._make_key(key),
                expiration,
                value
            )
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {str(e)}")
            return False
    
    def delete(self, key):
        """
        Delete a key from the cache
        
        Args:
            key (str): The key to delete
            
        Returns:
            bool: True if the key was deleted, False otherwise
        """
        try:
            self._connect()
            result = self._redis.delete(self._make_key(key))
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {str(e)}")
            return False
    
    def exists(self, key):
        """
        Check if a key exists in the cache
        
        Args:
            key (str): The key to check
            
        Returns:
            bool: True if the key exists, False otherwise
        """
        try:
            self._connect()
            return self._redis.exists(self._make_key(key)) > 0
        except Exception as e:
            logger.error(f"Error checking existence of key {key} in Redis: {str(e)}")
            return False
    
    def incr(self, key, amount=1):
        """
        Increment a key in the cache
        
        Args:
            key (str): The key to increment
            amount (int): The amount to increment by
            
        Returns:
            int: The new value, or None if there was an error
        """
        try:
            self._connect()
            return self._redis.incrby(self._make_key(key), amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key} in Redis: {str(e)}")
            return None
    
    def expire(self, key, time):
        """
        Set the expiration time for a key
        
        Args:
            key (str): The key to set expiration for
            time (int): The expiration time in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._connect()
            return self._redis.expire(self._make_key(key), time)
        except Exception as e:
            logger.error(f"Error setting expiration for key {key} in Redis: {str(e)}")
            return False
    
    def ttl(self, key):
        """
        Get the remaining time to live for a key
        
        Args:
            key (str): The key to check
            
        Returns:
            int: The remaining time in seconds, or None if there was an error
        """
        try:
            self._connect()
            return self._redis.ttl(self._make_key(key))
        except Exception as e:
            logger.error(f"Error getting TTL for key {key} from Redis: {str(e)}")
            return None
    
    def hset(self, key, field, value):
        """
        Set a hash field in the cache
        
        Args:
            key (str): The key of the hash
            field (str): The field to set
            value: The value to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._connect()
            # Serialize non-string values to JSON
            if not isinstance(value, (str, bytes, bytearray)):
                value = json.dumps(value)
            
            self._redis.hset(self._make_key(key), field, value)
            return True
        except Exception as e:
            logger.error(f"Error setting hash field {field} for key {key} in Redis: {str(e)}")
            return False
    
    def hget(self, key, field, default=None):
        """
        Get a hash field from the cache
        
        Args:
            key (str): The key of the hash
            field (str): The field to get
            default: The default value to return if the field doesn't exist
            
        Returns:
            The value of the field, or the default
        """
        try:
            self._connect()
            value = self._redis.hget(self._make_key(key), field)
            if value is None:
                return default
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # If not JSON, return the raw value
                return value
        except Exception as e:
            logger.error(f"Error getting hash field {field} for key {key} from Redis: {str(e)}")
            return default
    
    def hdel(self, key, field):
        """
        Delete a hash field from the cache
        
        Args:
            key (str): The key of the hash
            field (str): The field to delete
            
        Returns:
            bool: True if the field was deleted, False otherwise
        """
        try:
            self._connect()
            result = self._redis.hdel(self._make_key(key), field)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting hash field {field} for key {key} from Redis: {str(e)}")
            return False
    
    def hkeys(self, key):
        """
        Get all fields in a hash
        
        Args:
            key (str): The key of the hash
            
        Returns:
            list: A list of fields, or an empty list if there was an error
        """
        try:
            self._connect()
            keys = self._redis.hkeys(self._make_key(key))
            # Convert from bytes to string if necessary
            if keys and isinstance(keys[0], bytes):
                keys = [k.decode('utf-8') for k in keys]
            return keys
        except Exception as e:
            logger.error(f"Error getting hash keys for key {key} from Redis: {str(e)}")
            return []
    
    def clear_all(self):
        """
        Clear all keys in the cache
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._connect()
            self._redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Error clearing all keys from Redis: {str(e)}")
            return False
    
    def clear_namespace(self):
        """
        Clear all keys in the current namespace
        
        Returns:
            int: The number of keys deleted
        """
        try:
            self._connect()
            pattern = f"{self.namespace}:*"
            count = 0
            
            # Get all keys matching the pattern
            cursor = 0
            while True:
                cursor, keys = self._redis.scan(cursor, match=pattern, count=100)
                if keys:
                    count += len(keys)
                    self._redis.delete(*keys)
                if cursor == 0:
                    break
            
            return count
        except Exception as e:
            logger.error(f"Error clearing namespace {self.namespace} from Redis: {str(e)}")
            return 0
    
    def clear_pattern(self, pattern):
        """
        Clear keys matching a pattern
        
        Args:
            pattern (str): The pattern to match (will be prefixed with namespace)
            
        Returns:
            int: The number of keys deleted
        """
        try:
            self._connect()
            full_pattern = f"{self.namespace}:{pattern}"
            count = 0
            
            # Get all keys matching the pattern
            cursor = 0
            while True:
                cursor, keys = self._redis.scan(cursor, match=full_pattern, count=100)
                if keys:
                    count += len(keys)
                    self._redis.delete(*keys)
                if cursor == 0:
                    break
            
            return count
        except Exception as e:
            logger.error(f"Error clearing pattern {pattern} from Redis: {str(e)}")
            return 0
    
    def get_client_info(self):
        """
        Get information about the Redis client
        
        Returns:
            dict: Client information, or None if there was an error
        """
        try:
            self._connect()
            info = self._redis.info()
            return info
        except Exception as e:
            logger.error(f"Error getting Redis client info: {str(e)}")
            return None
    
    def pipeline(self):
        """
        Create a Redis pipeline for batching commands
        
        Returns:
            Pipeline: A Redis pipeline, or None if there was an error
        """
        try:
            self._connect()
            return self._redis.pipeline()
        except Exception as e:
            logger.error(f"Error creating Redis pipeline: {str(e)}")
            return None