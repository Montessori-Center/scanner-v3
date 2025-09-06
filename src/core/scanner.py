#!/usr/bin/env python3
"""Main scanner module for project analysis"""
import time
from pathlib import Path

from src.core.cache import PersistentCache
from src.core.config import Settings
from src.core.models import FileInfo, ScanResult


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
                except Exception:
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

    def _load_exclude_patterns(self):
        """Load patterns from config/exclude.conf"""
        patterns = []
        exclude_file = Path("config/exclude.conf")

        if exclude_file.exists():
            with open(exclude_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)

        if not patterns:
            patterns = self.settings.DEFAULT_EXCLUDE

        return patterns

    def _should_exclude(self, file_path: Path, root: Path) -> bool:
        """Check if file should be excluded"""
        try:
            relative = str(file_path.relative_to(root))

            if not hasattr(self, '_exclude_patterns'):
                self._exclude_patterns = self._load_exclude_patterns()

            for pattern in self._exclude_patterns:
                # Check both full path and relative path
                if file_path.match(pattern) or Path(relative).match(pattern):
                    return True
                # Check if pattern is in path string
                if pattern.strip("*/") in str(file_path):
                    return True

        except Exception:
            pass

        return False
