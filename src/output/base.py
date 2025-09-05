"""Base formatter class"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseFormatter(ABC):
    """Base class for all output formatters"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize formatter with optional config"""
        self.config = config or {}
    
    @abstractmethod
    def format(self, results: Dict[str, Any]) -> str:
        """Format analysis results
        
        Args:
            results: Dictionary with analysis results from all analyzers
            
        Returns:
            Formatted string representation
        """
        pass
    
    def get_name(self) -> str:
        """Get formatter name"""
        return self.__class__.__name__
