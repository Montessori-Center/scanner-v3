"""Dependency Injection container with auto-discovery"""
import pkgutil
import importlib
from typing import Dict, Type, Optional, List
from pathlib import Path

from src.core.base import BaseAnalyzer
from src.core.scanner import Scanner
from src.core.config import Settings
from src.core.logger import get_logger


class Container:
    """DI Container with automatic analyzer discovery"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self._scanner = Scanner(self.settings)
        self.logger = get_logger("container")
        self._analyzers = self._discover_analyzers()
        self._analyzers = self._discover_analyzers()
        self._failed_analyzers = {}  # Track failed analyzers
    
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
            self.logger.warning(f"Analyzers path not found: {analyzers_path}")
            return analyzers
        
        # Import analyzers package
        try:
            import src.analyzers as pkg
            
            # Find all modules in package
            for importer, modname, ispkg in pkgutil.iter_modules(
                pkg.__path__, 
                prefix=pkg.__name__ + "."
            ):
                if ispkg:
                    continue  # Skip subpackages
                    
                try:
                    # Import module
                    self.logger.debug(f"Attempting to import: {modname}")
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
                                self.logger.info(f"✓ Discovered analyzer: {name} ({item_name})")
                except ImportError as e:
                    self.logger.error(f"✗ Failed to import module {modname}: {e}")
                    self._failed_analyzers[modname] = str(e)
                except Exception as e:
                    self.logger.error(f"✗ Error processing module {modname}: {e}")
                    self._failed_analyzers[modname] = str(e)
                    
        except ImportError as e:
            self.logger.error(f"Failed to import analyzers package: {e}")
        
        self.logger.info(f"Total analyzers discovered: {len(analyzers)}")
        if self._failed_analyzers:
            self.logger.warning(f"Failed to load {len(self._failed_analyzers)} modules")
        
        return analyzers
    
    def get_analyzer(self, name: str) -> Optional[BaseAnalyzer]:
        """Get analyzer instance by name"""
        # Check if already instantiated
        if name in self._instances:
            return self._instances[name]
        
        # Create new instance
        if name in self._analyzers:
            try:
                instance = self._analyzers[name]()
                self._instances[name] = instance
                self.logger.debug(f"Created instance of analyzer: {name}")
                return instance
            except Exception as e:
                self.logger.error(f"Failed to instantiate analyzer {name}: {e}")
                self._failed_analyzers[name] = str(e)
                return None
        
        self.logger.warning(f"Analyzer not found: {name}")
        return None
    
    def list_analyzers(self) -> Dict[str, Type[BaseAnalyzer]]:
        """List all available analyzers"""
        return self._analyzers
    
    def get_analyzer_names(self) -> List[str]:
        """Get list of analyzer names"""
        return list(self._analyzers.keys())
    
    def get_failed_analyzers(self) -> Dict[str, str]:
        """Get dictionary of failed analyzers and their errors"""
        return self._failed_analyzers
    
    def get_status(self) -> Dict:
        """Get container status"""
        return {
            "loaded_analyzers": len(self._analyzers),
            "failed_analyzers": len(self._failed_analyzers),
            "instantiated": len(self._instances),
            "available": list(self._analyzers.keys()),
            "failed": list(self._failed_analyzers.keys())
        }
