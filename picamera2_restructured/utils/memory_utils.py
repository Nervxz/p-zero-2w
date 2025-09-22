"""
Memory optimization utilities.

This module provides utilities for optimizing memory usage,
especially important for resource-constrained devices like Raspberry Pi.
"""

import gc
import os
import tempfile
import numpy as np
import weakref
from typing import Dict, Any, Tuple, Optional, List, Union

class MemoryManager:
    """
    Memory manager for optimizing memory usage.
    
    Provides utilities for tracking and optimizing memory usage.
    """
    
    def __init__(self):
        """Initialize the memory manager."""
        self._objects = weakref.WeakSet()
        self._temp_files = []
    
    def register(self, obj):
        """
        Register an object for memory tracking.
        
        Args:
            obj: Object to track
        """
        self._objects.add(obj)
        return obj
    
    def optimize(self):
        """
        Optimize memory usage.
        
        Performs garbage collection and other memory optimizations.
        
        Returns:
            Number of objects collected
        """
        # Run garbage collection
        count = gc.collect()
        
        # Clean up any temporary files
        for temp_file in self._temp_files[:]:
            if os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    self._temp_files.remove(temp_file)
                except (IOError, OSError):
                    pass
        
        return count
    
    def create_temp_file(self, suffix=None):
        """
        Create a temporary file that will be cleaned up automatically.
        
        Args:
            suffix: Optional file suffix
            
        Returns:
            Path to the temporary file
        """
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        self._temp_files.append(path)
        return path
    
    def get_object_count(self):
        """
        Get the number of tracked objects.
        
        Returns:
            Number of tracked objects
        """
        return len(self._objects)
    
    def clear(self):
        """Clear all tracked objects."""
        self._objects.clear()
        
        # Clean up any temporary files
        for temp_file in self._temp_files[:]:
            if os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except (IOError, OSError):
                    pass
        self._temp_files.clear()

# Global memory manager instance
memory_manager = MemoryManager()

class MemoryOptimizedArray:
    """
    Memory-optimized array using memory mapping.
    
    Uses memory mapping to store large arrays on disk instead of in RAM,
    which is especially useful for resource-constrained devices.
    """
    
    def __init__(self, shape, dtype=np.float32, persistent=False):
        """
        Initialize a memory-optimized array.
        
        Args:
            shape: Shape of the array
            dtype: Data type of the array
            persistent: Whether to keep the file after the object is destroyed
        """
        self.shape = shape
        self.dtype = dtype
        self.persistent = persistent
        
        # Create a temporary file for the memory mapping
        if persistent:
            self.filename = f"memarray_{id(self)}.dat"
        else:
            self.filename = memory_manager.create_temp_file(suffix=".dat")
        
        # Create the memory-mapped array
        self.array = np.memmap(self.filename, dtype=dtype, mode='w+', shape=shape)
    
    def __getitem__(self, key):
        """Get an item from the array."""
        return self.array[key]
    
    def __setitem__(self, key, value):
        """Set an item in the array."""
        self.array[key] = value
    
    def __del__(self):
        """Clean up when the object is destroyed."""
        if hasattr(self, 'array'):
            # Flush any changes to disk
            self.array.flush()
            
            # Close the memmap
            del self.array
            
            # Remove the file if not persistent
            if not self.persistent and hasattr(self, 'filename'):
                if os.path.exists(self.filename):
                    try:
                        os.unlink(self.filename)
                    except (IOError, OSError):
                        pass

def optimize_memory():
    """
    Optimize memory usage.
    
    Performs garbage collection and other memory optimizations.
    
    Returns:
        Number of objects collected
    """
    return memory_manager.optimize()

def get_memory_usage():
    """
    Get current memory usage.
    
    Returns:
        Dictionary with memory usage information
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return {
            'rss': mem_info.rss,  # Resident Set Size
            'vms': mem_info.vms,  # Virtual Memory Size
            'percent': process.memory_percent()
        }
    except ImportError:
        # psutil not available, use a simpler approach
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return {
            'max_rss': usage.ru_maxrss * 1024,  # Convert to bytes
        }

def reduce_memory_usage(array):
    """
    Reduce memory usage of a numpy array by using a more efficient data type.
    
    Args:
        array: Numpy array to optimize
        
    Returns:
        Memory-optimized array
    """
    # Convert integer arrays to the smallest possible integer type
    if np.issubdtype(array.dtype, np.integer):
        min_val = array.min()
        max_val = array.max()
        
        if min_val >= 0:
            if max_val <= 255:
                return array.astype(np.uint8)
            elif max_val <= 65535:
                return array.astype(np.uint16)
            elif max_val <= 4294967295:
                return array.astype(np.uint32)
        else:
            if min_val >= -128 and max_val <= 127:
                return array.astype(np.int8)
            elif min_val >= -32768 and max_val <= 32767:
                return array.astype(np.int16)
            elif min_val >= -2147483648 and max_val <= 2147483647:
                return array.astype(np.int32)
    
    # Convert float arrays to float32 if possible
    if np.issubdtype(array.dtype, np.floating) and array.dtype != np.float32:
        return array.astype(np.float32)
    
    # Return the original array if no optimization is possible
    return array

class MemoryPool:
    """
    Memory pool for reusing memory buffers.
    
    Reduces memory allocations by reusing buffers of the same size.
    """
    
    def __init__(self):
        """Initialize the memory pool."""
        self._pools = {}
        self._lock = __import__('threading').RLock()
    
    def get(self, shape, dtype=np.float32):
        """
        Get a buffer from the pool or create a new one.
        
        Args:
            shape: Shape of the buffer
            dtype: Data type of the buffer
            
        Returns:
            Numpy array
        """
        with self._lock:
            key = (shape, dtype)
            
            # Check if we have a pool for this shape and dtype
            if key not in self._pools:
                self._pools[key] = []
            
            # Get a buffer from the pool or create a new one
            if self._pools[key]:
                buffer = self._pools[key].pop()
            else:
                buffer = np.zeros(shape, dtype=dtype)
            
            return buffer
    
    def put(self, buffer):
        """
        Return a buffer to the pool.
        
        Args:
            buffer: Numpy array to return to the pool
        """
        with self._lock:
            key = (buffer.shape, buffer.dtype)
            
            # Check if we have a pool for this shape and dtype
            if key not in self._pools:
                self._pools[key] = []
            
            # Return the buffer to the pool
            self._pools[key].append(buffer)
    
    def clear(self):
        """Clear all pools."""
        with self._lock:
            self._pools.clear()

# Global memory pool instance
memory_pool = MemoryPool()
