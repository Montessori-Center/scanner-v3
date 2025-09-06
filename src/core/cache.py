#!/usr/bin/env python3
"""Persistent cache for incremental scanning with atomic writes"""
import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict


class PersistentCache:
    """Cache on disk for incremental runs with atomic operations"""

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
            except (OSError, json.JSONDecodeError):
                # If cache is corrupted, start fresh
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
        """Save cache to disk atomically"""
        try:
            # Create temporary file in the same directory (for atomic rename)
            temp_fd, temp_path = tempfile.mkstemp(
                dir=str(self.cache_dir),
                prefix='.scanner_cache_',
                suffix='.tmp'
            )

            # Write to temporary file
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(self.cache_data, f, indent=2)

            # Atomic rename (on POSIX systems)
            # On Windows, we need to remove the target first
            temp_path_obj = Path(temp_path)
            if os.name == 'nt' and self.cache_file.exists():
                self.cache_file.unlink()

            # Rename temporary file to actual cache file
            temp_path_obj.rename(self.cache_file)

        except Exception as e:
            # Clean up temporary file if it exists
            try:
                if 'temp_path' in locals():
                    Path(temp_path).unlink(missing_ok=True)
            except:
                pass
            # Re-raise the original exception
            raise e

    def clear(self):
        """Clear the cache"""
        self.cache_data = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
