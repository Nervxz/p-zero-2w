"""
Module registry for optimizing module loading and management.

This module provides a registry for managing modules and their dependencies,
which can be used to optimize module loading and initialization.
"""

import importlib
import sys
import threading
from typing import Dict, Any, List, Set, Optional, Callable

class ModuleRegistry:
    """
    Registry for managing modules and their dependencies.
    
    Provides utilities for lazy loading, dependency management,
    and module initialization.
    """
    
    def __init__(self):
        """Initialize the module registry."""
        self._modules = {}
        self._dependencies = {}
        self._initialized = set()
        self._lock = threading.RLock()
    
    def register(self, name, module_path, dependencies=None):
        """
        Register a module with the registry.
        
        Args:
            name: Name of the module
            module_path: Import path of the module
            dependencies: List of module names that this module depends on
        """
        with self._lock:
            self._modules[name] = module_path
            self._dependencies[name] = set(dependencies or [])
    
    def get_module(self, name):
        """
        Get a module by name, loading it if necessary.
        
        Args:
            name: Name of the module
            
        Returns:
            Loaded module
        """
        with self._lock:
            # Check if the module is registered
            if name not in self._modules:
                raise ValueError(f"Module {name} is not registered")
            
            # Load the module
            module_path = self._modules[name]
            return importlib.import_module(module_path)
    
    def initialize(self, name):
        """
        Initialize a module and its dependencies.
        
        Args:
            name: Name of the module
        """
        with self._lock:
            # Check if the module is already initialized
            if name in self._initialized:
                return
            
            # Check if the module is registered
            if name not in self._modules:
                raise ValueError(f"Module {name} is not registered")
            
            # Initialize dependencies first
            for dependency in self._dependencies[name]:
                self.initialize(dependency)
            
            # Load and initialize the module
            module = self.get_module(name)
            if hasattr(module, 'initialize'):
                module.initialize()
            
            # Mark as initialized
            self._initialized.add(name)
    
    def initialize_all(self):
        """Initialize all registered modules."""
        with self._lock:
            # Sort modules by dependencies
            modules = self._sort_by_dependencies()
            
            # Initialize modules in order
            for name in modules:
                self.initialize(name)
    
    def _sort_by_dependencies(self):
        """
        Sort modules by dependencies.
        
        Returns:
            List of module names sorted by dependencies
        """
        # Build dependency graph
        graph = {name: list(deps) for name, deps in self._dependencies.items()}
        
        # Topological sort
        result = []
        visited = set()
        temp = set()
        
        def visit(node):
            if node in temp:
                raise ValueError(f"Circular dependency detected involving {node}")
            if node in visited:
                return
            
            temp.add(node)
            for neighbor in graph.get(node, []):
                visit(neighbor)
            
            temp.remove(node)
            visited.add(node)
            result.append(node)
        
        # Visit all nodes
        for name in self._modules:
            if name not in visited:
                visit(name)
        
        return result
    
    def get_initialized_modules(self):
        """
        Get the list of initialized modules.
        
        Returns:
            Set of initialized module names
        """
        with self._lock:
            return set(self._initialized)
    
    def clear(self):
        """Clear the registry."""
        with self._lock:
            self._modules.clear()
            self._dependencies.clear()
            self._initialized.clear()

# Global module registry instance
module_registry = ModuleRegistry()

def register_module(name, module_path, dependencies=None):
    """
    Register a module with the global registry.
    
    Args:
        name: Name of the module
        module_path: Import path of the module
        dependencies: List of module names that this module depends on
    """
    module_registry.register(name, module_path, dependencies)

def get_module(name):
    """
    Get a module from the global registry.
    
    Args:
        name: Name of the module
        
    Returns:
        Loaded module
    """
    return module_registry.get_module(name)

def initialize_module(name):
    """
    Initialize a module from the global registry.
    
    Args:
        name: Name of the module
    """
    module_registry.initialize(name)

def initialize_all_modules():
    """Initialize all modules in the global registry."""
    module_registry.initialize_all()

class ModuleLoader:
    """
    Module loader for optimizing module loading.
    
    Provides utilities for loading modules on-demand and managing
    their initialization.
    """
    
    def __init__(self, registry=None):
        """
        Initialize the module loader.
        
        Args:
            registry: Module registry to use, or None to use the global registry
        """
        self.registry = registry or module_registry
    
    def load(self, name):
        """
        Load a module by name.
        
        Args:
            name: Name of the module
            
        Returns:
            Loaded module
        """
        return self.registry.get_module(name)
    
    def load_and_initialize(self, name):
        """
        Load and initialize a module by name.
        
        Args:
            name: Name of the module
            
        Returns:
            Loaded and initialized module
        """
        self.registry.initialize(name)
        return self.registry.get_module(name)
    
    def load_multiple(self, names):
        """
        Load multiple modules by name.
        
        Args:
            names: List of module names
            
        Returns:
            Dictionary mapping module names to loaded modules
        """
        return {name: self.load(name) for name in names}
    
    def load_and_initialize_multiple(self, names):
        """
        Load and initialize multiple modules by name.
        
        Args:
            names: List of module names
            
        Returns:
            Dictionary mapping module names to loaded and initialized modules
        """
        return {name: self.load_and_initialize(name) for name in names}

# Global module loader instance
module_loader = ModuleLoader()
