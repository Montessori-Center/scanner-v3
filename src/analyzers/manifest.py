#!/usr/bin/env python3
"""Manifest analyzer - project structure and metadata"""
from typing import Dict, List

from src.core.base import BaseAnalyzer
from src.core.constants import Limits
from src.core.logger import get_logger
from src.core.models import AnalysisResult, ScanResult


class ManifestAnalyzer(BaseAnalyzer):
    """Analyze project structure and basic metadata"""

    name = "manifest"
    description = "Project structure and metadata analysis"

    logger = get_logger("manifest")

    async def analyze(self, scan: ScanResult) -> AnalysisResult:
        """Analyze project manifest"""

        # Count files by extension
        extensions: Dict[str, int] = {}
        languages: Dict[str, int] = {}

        for file in scan.files:
            ext = file.extension.lower()
            extensions[ext] = extensions.get(ext, 0) + 1

            # Map to languages
            lang = self._map_to_language(ext)
            if lang:
                languages[lang] = languages.get(lang, 0) + 1

        # Find entry points
        entry_points = self._find_entry_points(scan)

        # Detect project type
        project_type = self._detect_project_type(scan)

        # Get top directories
        directories = self._get_directories(scan)

        return AnalysisResult(
            analyzer=self.name,
            data={
                "project_type": project_type,
                "project_path": str(scan.root),
                "total_files": scan.total_files,
                "total_size": scan.total_size,
                "scan_duration": scan.duration,
                "languages": languages,
                "extensions": extensions,
                "entry_points": entry_points,
                "directories": directories[:Limits.MAX_DIRECTORIES_TO_SHOW],  # Top 20 dirs
                "has_git": (scan.root / ".git").exists(),
                "has_tests": self._has_tests(scan),
                "has_docs": self._has_docs(scan),
                "has_ci": self._has_ci(scan),
            }
        )

    def _map_to_language(self, ext: str) -> str:
        """Map file extension to language"""
        mapping = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.php': 'php',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.m': 'matlab',
            '.lua': 'lua',
            '.dart': 'dart',
        }
        return mapping.get(ext, '')

    def _detect_project_type(self, scan: ScanResult) -> str:
        """Detect project type from files"""
        root = scan.root

        # Check for specific files
        if (root / "package.json").exists():
            if (root / "next.config.js").exists():
                return "nextjs"
            if (root / "gatsby-config.js").exists():
                return "gatsby"
            if (root / "angular.json").exists():
                return "angular"
            if (root / "vue.config.js").exists():
                return "vue"
            return "nodejs"

        if (root / "requirements.txt").exists() or (root / "setup.py").exists():
            if (root / "manage.py").exists():
                return "django"
            if (root / "app.py").exists() or (root / "application.py").exists():
                return "flask"
            return "python"

        if (root / "composer.json").exists():
            if (root / "artisan").exists():
                return "laravel"
            if (root / "symfony.lock").exists():
                return "symfony"
            return "php"

        if (root / "Cargo.toml").exists():
            return "rust"

        if (root / "go.mod").exists():
            return "go"

        if (root / "pom.xml").exists():
            return "java-maven"

        if (root / "build.gradle").exists():
            return "java-gradle"

        if (root / "Gemfile").exists():
            return "ruby"

        return "unknown"

    def _find_entry_points(self, scan: ScanResult) -> List[str]:
        """Find project entry points"""
        entry_points = []
        common_names = [
            "main.py", "app.py", "index.py", "run.py", "__main__.py",
            "index.js", "app.js", "main.js", "server.js",
            "index.php", "app.php",
            "main.go", "main.rs", "main.java", "main.cpp",
            "index.html", "index.htm"
        ]

        for file in scan.files:
            if file.name in common_names:
                entry_points.append(str(file.path.relative_to(scan.root)))

        return entry_points[:Limits.MAX_ENTRY_POINTS]  # Max 10 entry points

    def _get_directories(self, scan: ScanResult) -> List[str]:
        """Get unique directories"""
        dirs = set()
        for file in scan.files:
            parent = file.path.parent
            if parent != scan.root:
                try:
                    dirs.add(str(parent.relative_to(scan.root)))
                except ValueError as e:
                    self.logger.debug(f"Path {parent} not relative to {scan.root}: {e}")
        return sorted(list(dirs))

    def _has_tests(self, scan: ScanResult) -> bool:
        """Check if project has tests"""
        test_dirs = {'test', 'tests', '__tests__', 'spec', 'specs'}
        for file in scan.files:
            parts = file.path.parts
            if any(part in test_dirs for part in parts):
                return True
        return False

    def _has_docs(self, scan: ScanResult) -> bool:
        """Check if project has documentation"""
        doc_files = {'README.md', 'README.rst', 'README.txt', 'docs', 'documentation'}
        for file in scan.files:
            if file.name in doc_files or 'docs' in file.path.parts:
                return True
        return False

    def _has_ci(self, scan: ScanResult) -> bool:
        """Check if project has CI/CD"""
        ci_files = {'.github', '.gitlab-ci.yml', '.travis.yml', 'Jenkinsfile', '.circleci'}
        for file in scan.files:
            if any(ci in str(file.path) for ci in ci_files):
                return True
        return False
