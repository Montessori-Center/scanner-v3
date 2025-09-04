"""Main scanner module for project analysis"""
from pathlib import Path
from typing import List
import asyncio
import time
from fnmatch import fnmatch

from src.core.cache import PersistentCache
from src.core.config import Settings
from src.core.models import ScanResult, FileInfo


class Scanner:
    """Main project scanner with cache integration"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.cache = None
    
    async def scan(self, project_path: Path) -> ScanResult:
        """Scan project with cache support"""
        start_time = time.time()
        
        # Initialize cache
        cache_dir = project_path / ".scanner_cache"
        self.cache = PersistentCache(cache_dir)
        
        files = []
        profile = self.settings.get_profile_settings()
        max_size = profile["max_file_size"]
        
        # Scan files
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                # Check exclusions
                if self._should_exclude(file_path, project_path):
                    continue
                
                # Check size
                try:
                    if file_path.stat().st_size > max_size:
                        continue
                except:
                    continue
                
                # Add to results
                files.append(FileInfo(
                    path=file_path,
                    size=file_path.stat().st_size,
                    extension=file_path.suffix
                ))
                
                # Update cache
                if self.cache.is_file_changed(file_path):
                    self.cache.update_file(file_path)
        
        # Save cache
        self.cache.save()
        
        duration = time.time() - start_time
        
        return ScanResult(
            root=project_path,
            files=files,
            total_files=len(files),
            total_size=sum(f.size for f in files),
            duration=duration
        )
    
    def _should_exclude(self, file_path: Path, root: Path) -> bool:
        """Check if file should be excluded"""
        try:
            relative = str(file_path.relative_to(root))
            
            for pattern in self.settings.DEFAULT_EXCLUDE:
                # Simple pattern matching
                pattern_clean = pattern.replace("**", "*")
                if "*" in pattern_clean:
                    if fnmatch(relative, pattern_clean):
                        return True
                else:
                    # Direct substring match
                    if pattern_clean.strip("*/") in relative:
                        return True
        except:
            pass
        
        return False
