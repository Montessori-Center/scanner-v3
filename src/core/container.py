"""Dependency Injection container with auto-discovery"""
import pkgutil
import importlib
from typing import Dict, Type, Optional, List
from pathlib import Path

from src.core.base import BaseAnalyzer
from src.core.scanner import Scanner
from src.core.config import Settings


class Container:
    """DI Container with automatic analyzer discovery"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self._scanner = Scanner(self.settings)
        self._analyzers = self._discover_analyzers()
        self._instances = {}
    
    @property
    def scanner(self) -> Scanner:
        """Get scanner instance"""
        return self._scanner
    
    def _discover_analyzers(self) -> Dict[str, Type[BaseAnalyzer]]:
        """Automatically discover all analyzers via pkgutil"""
        analyzers = {}
        
        # Get analyzers package path
        analyzers_path = Path(__file__).parent.parent / "analyzers"
        
        if not analyzers_path.exists():
            return analyzers
        
        # Import analyzers package
        try:
            import src.analyzers as pkg
            
            # Find all modules in package
            for importer, modname, ispkg in pkgutil.iter_modules(
                pkg.__path__, 
                prefix=pkg.__name__ + "."
            ):
                try:
                    # Import module
                    module = importlib.import_module(modname)
                    
                    # Find analyzer classes
                    for item_name in dir(module):
                        if item_name.endswith('Analyzer') and item_name != 'BaseAnalyzer':
                            analyzer_class = getattr(module, item_name)
                            # Check if it's a subclass of BaseAnalyzer
                            if isinstance(analyzer_class, type) and issubclass(analyzer_class, BaseAnalyzer):
                                # Use analyzer's name attribute
                                name = getattr(analyzer_class, 'name', modname.split('.')[-1])
                                analyzers[name] = analyzer_class
                except Exception as e:
                    # Skip modules that fail to import
                    pass
        except ImportError:
            # Analyzers package not ready yet
            pass
        
        return analyzers
    
    def get_analyzer(self, name: str) -> Optional[BaseAnalyzer]:
        """Get analyzer instance by name"""
        # Check if already instantiated
        if name in self._instances:
            return self._instances[name]
        
        # Create new instance
        if name in self._analyzers:
            instance = self._analyzers[name]()
            self._instances[name] = instance
            return instance
        
        return None
    
    def list_analyzers(self) -> Dict[str, Type[BaseAnalyzer]]:
        """List all available analyzers"""
        return self._analyzers
    
    def get_analyzer_names(self) -> List[str]:
        """Get list of analyzer names"""
        return list(self._analyzers.keys())
