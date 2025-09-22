"""
Utility functions and helper modules for PiCamera2.

This module provides various utility functions and helpers that can be used
across the library or by end users to work with camera data and configurations.
"""

from .image_utils import ImageUtils
from .format_utils import FormatUtils
from .cache_utils import memoize, thread_local_cache, ResourceCache, get_cached_label, ImageCache
from .memory_utils import MemoryManager, MemoryOptimizedArray, optimize_memory, get_memory_usage, reduce_memory_usage, MemoryPool, memory_pool, memory_manager
from .parallel_utils import ThreadPool, parallel_map, WorkerPool, BatchProcessor
from .profiling_utils import Timer, timing_decorator, Profiler, profile_decorator, PerformanceTracker, track_performance, performance_tracker
from .image_optimization_utils import optimize_image, fast_resize, fast_convert_color, fast_gaussian_blur, vectorized_histogram, fast_threshold, batch_process_images, optimize_bounding_boxes, draw_optimized_boxes

__all__ = [
    # Original utils
    'ImageUtils',
    'FormatUtils',
    
    # Cache utils
    'memoize',
    'thread_local_cache',
    'ResourceCache',
    'get_cached_label',
    'ImageCache',
    
    # Memory utils
    'MemoryManager',
    'MemoryOptimizedArray',
    'optimize_memory',
    'get_memory_usage',
    'reduce_memory_usage',
    'MemoryPool',
    'memory_pool',
    'memory_manager',
    
    # Parallel utils
    'ThreadPool',
    'parallel_map',
    'WorkerPool',
    'BatchProcessor',
    
    # Profiling utils
    'Timer',
    'timing_decorator',
    'Profiler',
    'profile_decorator',
    'PerformanceTracker',
    'track_performance',
    'performance_tracker',
    
    # Image optimization utils
    'optimize_image',
    'fast_resize',
    'fast_convert_color',
    'fast_gaussian_blur',
    'vectorized_histogram',
    'fast_threshold',
    'batch_process_images',
    'optimize_bounding_boxes',
    'draw_optimized_boxes',
]
