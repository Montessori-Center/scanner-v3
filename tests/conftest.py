#!/usr/bin/env python3
"""Shared fixtures for tests"""
import shutil
import tempfile
from pathlib import Path

import pytest

from src.core.config import Settings
from src.core.models import FileInfo, ScanResult
from src.core.scanner import Scanner


@pytest.fixture
def temp_project():
    """Create a temporary project structure for testing"""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)

    # Create basic project structure
    (project_path / "src").mkdir()
    (project_path / "tests").mkdir()
    (project_path / "docs").mkdir()

    # Create some test files
    (project_path / "README.md").write_text("# Test Project\nThis is a test project.")
    (project_path / "requirements.txt").write_text("pytest==7.4.0\nflask==2.3.0")
    (project_path / ".env").write_text("API_KEY=test123\nDATABASE_URL=postgresql://localhost/test")

    # Create Python files
    (project_path / "src" / "__init__.py").touch()
    (project_path / "src" / "main.py").write_text("""
def hello_world():
    '''Returns a greeting'''
    return "Hello, World!"

class TestClass:
    def __init__(self):
        self.value = 42

# TODO: Add more features
# FIXME: Handle edge cases
""")

    # Create API file
    (project_path / "src" / "api.py").write_text("""
from flask import Flask

app = Flask(__name__)

@app.route('/api/users')
def get_users():
    return {"users": []}

@app.route('/api/posts', methods=['POST'])
def create_post():
    return {"status": "created"}
""")

    yield project_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_scan_result(temp_project):
    """Create a mock scan result"""
    files = []
    for file_path in temp_project.rglob("*"):
        if file_path.is_file():
            files.append(FileInfo(
                path=file_path,
                size=file_path.stat().st_size,
                extension=file_path.suffix
            ))

    return ScanResult(
        root=temp_project,
        files=files,
        total_files=len(files),
        total_size=sum(f.size for f in files),
        duration=0.1
    )


@pytest.fixture
def test_settings():
    """Test settings"""
    return Settings(
        profile="fast",
        max_file_size=100000,
        scan_timeout=10
    )
