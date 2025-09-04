"""Base class for all analyzers"""
from abc import ABC, abstractmethod
from src.core.models import ScanResult, AnalysisResult


class BaseAnalyzer(ABC):
    """Base class for all analyzer modules"""
    
    name: str = "base"
    description: str = "Base analyzer"
    
    @abstractmethod
    async def analyze(self, scan: ScanResult) -> AnalysisResult:
        """Analyze scan results
        
        Args:
            scan: Results from project scanning
            
        Returns:
            AnalysisResult with analyzer data
        """
        pass
    
    def get_name(self) -> str:
        """Get analyzer name"""
        return self.name
    
    def get_description(self) -> str:
        """Get analyzer description"""
        return self.description
