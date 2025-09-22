"""
Cache utilities for optimizing performance.

This module provides caching decorators and utilities to improve performance
by avoiding redundant computations and storing frequently used results.
"""

from functools import lru_cache, wraps
import time
import hashlib
import threading
import weakref

# Thread-local storage for caches
_local_cache = threading.local()

def memoize(maxsize=128, timeout=None):
    """
    Memoization decorator with optional timeout.
    
    Args:
        maxsize (int): Maximum cache size
        timeout (float): Cache timeout in seconds, or None for no timeout
        
    Returns:
        Decorated function with memoization
    """
    cache = {}
    timestamps = {}
    lock = threading.RLock()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a hashable key from the arguments
            key_parts = [repr(arg) for arg in args]
            key_parts.extend(f"{k}:{repr(v)}" for k, v in sorted(kwargs.items()))
            key = hashlib.md5(str(key_parts).encode()).hexdigest()
            
            with lock:
                # Check if result is cached and not expired
                if key in cache:
                    if timeout is None or time.time() - timestamps[key] < timeout:
                        return cache[key]
                
                # Compute and cache the result
                result = func(*args, **kwargs)
                
                # Manage cache size
                if len(cache) >= maxsize:
                    # Remove oldest entry
                    oldest_key = min(timestamps.items(), key=lambda x: x[1])[0]
                    cache.pop(oldest_key)
                    timestamps.pop(oldest_key)
                
                cache[key] = result
                timestamps[key] = time.time()
                return result
                
        # Add cache management methods
        def clear_cache():
            with lock:
                cache.clear()
                timestamps.clear()
        
        wrapper.clear_cache = clear_cache
        return wrapper
    
    return decorator

def thread_local_cache(maxsize=128):
    """
    Thread-local cache decorator.
    
    Creates a separate cache for each thread to avoid lock contention.
    
    Args:
        maxsize (int): Maximum cache size per thread
        
    Returns:
        Decorated function with thread-local caching
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get or create thread-local cache
            if not hasattr(_local_cache, 'caches'):
                _local_cache.caches = {}
            
            if func.__name__ not in _local_cache.caches:
                _local_cache.caches[func.__name__] = {}
            
            cache = _local_cache.caches[func.__name__]
            
            # Create a hashable key from the arguments
            key_parts = [repr(arg) for arg in args]
            key_parts.extend(f"{k}:{repr(v)}" for k, v in sorted(kwargs.items()))
            key = hashlib.md5(str(key_parts).encode()).hexdigest()
            
            # Check if result is cached
            if key in cache:
                return cache[key]
            
            # Compute and cache the result
            result = func(*args, **kwargs)
            
            # Manage cache size
            if len(cache) >= maxsize:
                # Remove random entry (simple approach for thread safety)
                cache.pop(next(iter(cache)))
            
            cache[key] = result
            return result
        
        # Add cache management method
        def clear_cache():
            if hasattr(_local_cache, 'caches') and func.__name__ in _local_cache.caches:
                _local_cache.caches[func.__name__].clear()
        
        wrapper.clear_cache = clear_cache
        return wrapper
    
    return decorator

class ResourceCache:
    """
    Resource cache with automatic cleanup of unused resources.
    
    Uses weak references to allow resources to be garbage collected
    when they are no longer referenced elsewhere.
    """
    
    def __init__(self):
        self._cache = weakref.WeakValueDictionary()
        self._lock = threading.RLock()
    
    def get(self, key, factory_func):
        """
        Get a resource from cache or create it if not present.
        
        Args:
            key: Cache key
            factory_func: Function to create the resource if not in cache
            
        Returns:
            The cached or newly created resource
        """
        with self._lock:
            if key not in self._cache:
                self._cache[key] = factory_func()
            return self._cache[key]
    
    def clear(self):
        """Clear all cached resources."""
        with self._lock:
            self._cache.clear()
            
    def __len__(self):
        """Return the number of cached resources."""
        return len(self._cache)

# Optimized label caching
@lru_cache(maxsize=128)
def get_cached_label(labels_tuple, class_id, default="Unknown"):
    """
    Get a label from a tuple of labels with caching.
    
    Args:
        labels_tuple: Tuple of labels (must be a tuple for caching)
        class_id: Class ID to look up
        default: Default value if class_id is out of range
        
    Returns:
        The label string
    """
    if 0 <= class_id < len(labels_tuple):
        return labels_tuple[class_id]
    return f"{default}({class_id})"

# Image processing cache
class ImageCache:
    """
    Cache for processed images.
    
    Optimizes image processing by caching results based on operation
    and parameters.
    """
    
    def __init__(self, maxsize=32):
        self.maxsize = maxsize
        self.cache = {}
        self.timestamps = {}
        self.lock = threading.RLock()
    
    def get(self, image_hash, operation, **params):
        """
        Get a processed image from cache or process it.
        
        Args:
            image_hash: Hash of the input image
            operation: Processing operation function
            **params: Parameters for the operation
            
        Returns:
            Processed image
        """
        # Create a key from the operation and parameters
        param_str = str(sorted(params.items()))
        key = f"{image_hash}:{operation.__name__}:{param_str}"
        
        with self.lock:
            if key in self.cache:
                # Update timestamp and return cached result
                self.timestamps[key] = time.time()
                return self.cache[key]
            
            # Cache is full, remove least recently used item
            if len(self.cache) >= self.maxsize:
                oldest_key = min(self.timestamps.items(), key=lambda x: x[1])[0]
                self.cache.pop(oldest_key)
                self.timestamps.pop(oldest_key)
            
            # Not in cache, needs to be computed
            return None
    
    def put(self, image_hash, operation, result, **params):
        """
        Store a processed image in the cache.
        
        Args:
            image_hash: Hash of the input image
            operation: Processing operation function
            result: Result to cache
            **params: Parameters used for the operation
        """
        # Create a key from the operation and parameters
        param_str = str(sorted(params.items()))
        key = f"{image_hash}:{operation.__name__}:{param_str}"
        
        with self.lock:
            self.cache[key] = result
            self.timestamps[key] = time.time()
    
    def clear(self):
        """Clear the cache."""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
