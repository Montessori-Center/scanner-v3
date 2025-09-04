"""Persistent cache for incremental scanning"""
import json
import hashlib
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class PersistentCache:
    """Cache on disk for incremental runs"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = cache_dir / ".scanner_cache.json"
        self.cache_data = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return ""
    
    def is_file_changed(self, file_path: Path) -> bool:
        """Check if file changed since last scan"""
        key = str(file_path)
        if key not in self.cache_data:
            return True
            
        cached = self.cache_data[key]
        try:
            stat = file_path.stat()
            # Check mtime and size
            return (cached["mtime"] != stat.st_mtime or 
                    cached["size"] != stat.st_size)
        except:
            return True
    
    def update_file(self, file_path: Path):
        """Update cache for a file"""
        try:
            stat = file_path.stat()
            self.cache_data[str(file_path)] = {
                "mtime": stat.st_mtime,
                "size": stat.st_size,
                "hash": self._calculate_hash(file_path),
                "scanned": datetime.now().isoformat()
            }
        except:
            pass
    
    def save(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_data, f, indent=2)
        except:
            pass
