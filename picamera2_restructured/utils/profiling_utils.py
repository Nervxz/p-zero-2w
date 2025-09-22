"""
Profiling utilities for performance optimization.

This module provides utilities for profiling and benchmarking code
to identify performance bottlenecks.
"""

import time
import functools
import cProfile
import pstats
import io
import threading
from typing import Dict, Any, Callable, Optional, List, Union

class Timer:
    """
    Simple timer for measuring execution time.
    
    Example:
        with Timer("Operation"):
            # Code to measure
            pass
    """
    
    def __init__(self, name=None, verbose=True):
        """
        Initialize the timer.
        
        Args:
            name: Name of the operation being timed
            verbose: Whether to print the timing information
        """
        self.name = name or "Operation"
        self.verbose = verbose
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        """Start the timer."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer and print the timing information."""
        self.end_time = time.time()
        if self.verbose:
            elapsed = self.elapsed()
            if elapsed >= 1.0:
                print(f"{self.name} took {elapsed:.2f} seconds")
            elif elapsed >= 0.001:
                print(f"{self.name} took {elapsed*1000:.2f} ms")
            else:
                print(f"{self.name} took {elapsed*1000000:.2f} µs")
    
    def elapsed(self):
        """
        Get the elapsed time.
        
        Returns:
            Elapsed time in seconds
        """
        if self.start_time is None:
            return 0
        end_time = self.end_time or time.time()
        return end_time - self.start_time

def timing_decorator(func=None, *, name=None, verbose=True):
    """
    Decorator for timing function execution.
    
    Args:
        func: Function to time
        name: Name of the operation being timed
        verbose: Whether to print the timing information
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            timer_name = name or f.__name__
            with Timer(timer_name, verbose):
                return f(*args, **kwargs)
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)

class Profiler:
    """
    Profiler for detailed performance analysis.
    
    Example:
        with Profiler("My Profiler"):
            # Code to profile
            pass
    """
    
    def __init__(self, name=None, sort_by='cumulative', lines=20):
        """
        Initialize the profiler.
        
        Args:
            name: Name of the profiler
            sort_by: Sorting criteria for the profiling results
            lines: Number of lines to print in the profiling results
        """
        self.name = name or "Profiler"
        self.sort_by = sort_by
        self.lines = lines
        self.profiler = None
    
    def __enter__(self):
        """Start the profiler."""
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the profiler and print the profiling results."""
        self.profiler.disable()
        
        # Print the profiling results
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s).sort_stats(self.sort_by)
        ps.print_stats(self.lines)
        
        print(f"--- {self.name} Profiling Results ---")
        print(s.getvalue())

def profile_decorator(func=None, *, name=None, sort_by='cumulative', lines=20):
    """
    Decorator for profiling function execution.
    
    Args:
        func: Function to profile
        name: Name of the profiler
        sort_by: Sorting criteria for the profiling results
        lines: Number of lines to print in the profiling results
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            profiler_name = name or f.__name__
            with Profiler(profiler_name, sort_by, lines):
                return f(*args, **kwargs)
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)

class PerformanceTracker:
    """
    Track performance metrics over time.
    
    Useful for monitoring performance trends during long-running operations.
    """
    
    def __init__(self, window_size=100):
        """
        Initialize the performance tracker.
        
        Args:
            window_size: Number of measurements to keep in the window
        """
        self.window_size = window_size
        self.metrics = {}
        self._lock = threading.RLock()
    
    def record(self, metric_name, value):
        """
        Record a performance metric.
        
        Args:
            metric_name: Name of the metric
            value: Value of the metric
        """
        with self._lock:
            if metric_name not in self.metrics:
                self.metrics[metric_name] = []
            
            self.metrics[metric_name].append(value)
            
            # Keep only the last window_size measurements
            if len(self.metrics[metric_name]) > self.window_size:
                self.metrics[metric_name] = self.metrics[metric_name][-self.window_size:]
    
    def get_stats(self, metric_name):
        """
        Get statistics for a metric.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            if metric_name not in self.metrics or not self.metrics[metric_name]:
                return {
                    'count': 0,
                    'min': None,
                    'max': None,
                    'mean': None,
                    'median': None
                }
            
            values = self.metrics[metric_name]
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'mean': sum(values) / len(values),
                'median': sorted(values)[len(values) // 2]
            }
    
    def clear(self, metric_name=None):
        """
        Clear performance metrics.
        
        Args:
            metric_name: Name of the metric to clear, or None to clear all
        """
        with self._lock:
            if metric_name is None:
                self.metrics.clear()
            elif metric_name in self.metrics:
                self.metrics[metric_name] = []

# Global performance tracker instance
performance_tracker = PerformanceTracker()

def track_performance(func=None, *, metric_name=None):
    """
    Decorator for tracking function performance.
    
    Args:
        func: Function to track
        metric_name: Name of the metric
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = f(*args, **kwargs)
            elapsed_time = time.time() - start_time
            
            # Record the performance metric
            metric = metric_name or f.__name__
            performance_tracker.record(metric, elapsed_time)
            
            return result
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)
