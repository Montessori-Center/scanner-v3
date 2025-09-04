"""Data models for Scanner v3"""
from pydantic import BaseModel, Field
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class FileInfo(BaseModel):
    """Information about a single file"""
    path: Path
    size: int
    extension: str
    
    @property
    def name(self) -> str:
        return self.path.name
    
    @property
    def suffix(self) -> str:
        return self.path.suffix
    
    def read_text(self, errors: str = 'ignore') -> str:
        """Read file text content"""
        return self.path.read_text(errors=errors)
    
    def relative_to(self, other: Path) -> Path:
        """Get relative path"""
        return self.path.relative_to(other)
    
    class Config:
        arbitrary_types_allowed = True


class ScanResult(BaseModel):
    """Results of project scanning"""
    root: Path
    files: List[FileInfo]
    total_files: int
    total_size: int
    duration: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True


class AnalysisResult(BaseModel):
    """Results from an analyzer"""
    analyzer: str
    data: Dict[str, Any]
    errors: List[str] = []
    warnings: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True
