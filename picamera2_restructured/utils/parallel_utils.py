"""
Parallel processing utilities for optimizing performance.

This module provides utilities for parallel processing using threads
and processes to improve performance on multi-core systems.
"""

import threading
import multiprocessing
import queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
from typing import List, Callable, Any, Optional, Tuple, Dict, Union

class ThreadPool:
    """
    Thread pool for parallel execution of tasks.
    
    Optimized for camera processing workloads with minimal overhead.
    """
    
    def __init__(self, num_threads=None):
        """
        Initialize the thread pool.
        
        Args:
            num_threads: Number of worker threads, or None for auto-detection
        """
        self.num_threads = num_threads or max(1, multiprocessing.cpu_count() - 1)
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.workers = []
        self.running = False
        self._lock = threading.RLock()
    
    def start(self):
        """Start the worker threads."""
        with self._lock:
            if self.running:
                return
                
            self.running = True
            self.workers = []
            
            for _ in range(self.num_threads):
                worker = threading.Thread(target=self._worker_loop, daemon=True)
                worker.start()
                self.workers.append(worker)
    
    def stop(self):
        """Stop the worker threads."""
        with self._lock:
            self.running = False
            
            # Add None tasks to signal workers to exit
            for _ in range(self.num_threads):
                self.task_queue.put(None)
            
            # Wait for workers to finish
            for worker in self.workers:
                worker.join(timeout=1.0)
            
            self.workers = []
    
    def _worker_loop(self):
        """Worker thread main loop."""
        while self.running:
            try:
                # Get task from queue
                task = self.task_queue.get(timeout=0.1)
                
                # None is a signal to exit
                if task is None:
                    break
                
                # Unpack task
                task_id, func, args, kwargs = task
                
                # Execute task
                try:
                    result = func(*args, **kwargs)
                    self.result_queue.put((task_id, result, None))
                except Exception as e:
                    self.result_queue.put((task_id, None, e))
                
                # Mark task as done
                self.task_queue.task_done()
                
            except queue.Empty:
                continue
    
    def submit(self, func, *args, **kwargs):
        """
        Submit a task to the thread pool.
        
        Args:
            func: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Task ID
        """
        with self._lock:
            if not self.running:
                self.start()
            
            task_id = id(func) + time.time()
            self.task_queue.put((task_id, func, args, kwargs))
            return task_id
    
    def get_result(self, timeout=None):
        """
        Get a result from the result queue.
        
        Args:
            timeout: Timeout in seconds, or None to wait indefinitely
            
        Returns:
            Tuple of (task_id, result, exception)
        """
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None

def parallel_map(func, items, num_workers=None, use_processes=False):
    """
    Apply a function to each item in parallel.
    
    Args:
        func: Function to apply
        items: Items to process
        num_workers: Number of workers, or None for auto-detection
        use_processes: Use processes instead of threads
        
    Returns:
        List of results
    """
    executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
    num_workers = num_workers or max(1, multiprocessing.cpu_count() - 1)
    
    with executor_class(max_workers=num_workers) as executor:
        return list(executor.map(func, items))

class WorkerPool:
    """
    Flexible worker pool that can use either threads or processes.
    
    Optimized for camera processing with minimal overhead.
    """
    
    def __init__(self, num_workers=None, use_processes=False):
        """
        Initialize the worker pool.
        
        Args:
            num_workers: Number of workers, or None for auto-detection
            use_processes: Use processes instead of threads
        """
        self.num_workers = num_workers or max(1, multiprocessing.cpu_count() - 1)
        self.use_processes = use_processes
        self.executor = None
        self._lock = threading.RLock()
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    def start(self):
        """Start the worker pool."""
        with self._lock:
            if self.executor is not None:
                return
                
            executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
            self.executor = executor_class(max_workers=self.num_workers)
    
    def stop(self):
        """Stop the worker pool."""
        with self._lock:
            if self.executor is not None:
                self.executor.shutdown()
                self.executor = None
    
    def submit(self, func, *args, **kwargs):
        """
        Submit a task to the worker pool.
        
        Args:
            func: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Future object
        """
        with self._lock:
            if self.executor is None:
                self.start()
                
            return self.executor.submit(func, *args, **kwargs)
    
    def map(self, func, items):
        """
        Apply a function to each item in parallel.
        
        Args:
            func: Function to apply
            items: Items to process
            
        Returns:
            List of results
        """
        with self._lock:
            if self.executor is None:
                self.start()
                
            return list(self.executor.map(func, items))

class BatchProcessor:
    """
    Process items in batches for better efficiency.
    
    Optimized for image processing workloads.
    """
    
    def __init__(self, process_func, batch_size=4, num_workers=None, use_processes=False):
        """
        Initialize the batch processor.
        
        Args:
            process_func: Function to process each batch
            batch_size: Size of each batch
            num_workers: Number of workers, or None for auto-detection
            use_processes: Use processes instead of threads
        """
        self.process_func = process_func
        self.batch_size = batch_size
        self.worker_pool = WorkerPool(num_workers, use_processes)
        self.worker_pool.start()
    
    def process(self, items):
        """
        Process items in batches.
        
        Args:
            items: Items to process
            
        Returns:
            List of results
        """
        # Split items into batches
        batches = [items[i:i+self.batch_size] for i in range(0, len(items), self.batch_size)]
        
        # Process batches in parallel
        batch_results = self.worker_pool.map(self.process_func, batches)
        
        # Flatten results
        results = []
        for batch_result in batch_results:
            results.extend(batch_result)
        
        return results
    
    def close(self):
        """Close the batch processor."""
        self.worker_pool.stop()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
