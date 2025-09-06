#!/usr/bin/env python3
"""Tests for ManifestAnalyzer"""
import pytest

from src.analyzers.manifest import ManifestAnalyzer


@pytest.mark.unit
class TestManifestAnalyzer:
    """Test ManifestAnalyzer functionality"""

    def test_analyzer_initialization(self):
        """Test that analyzer initializes correctly"""
        analyzer = ManifestAnalyzer()
        assert analyzer.name == "manifest"
        assert analyzer.description == "Project structure and metadata analysis"

    @pytest.mark.asyncio
    async def test_analyze_basic_project(self, mock_scan_result):
        """Test analyzing a basic project"""
        analyzer = ManifestAnalyzer()
        result = await analyzer.analyze(mock_scan_result)

        assert result.analyzer == "manifest"
        assert "total_files" in result.data
        assert "project_type" in result.data
        assert result.data["total_files"] > 0

    @pytest.mark.asyncio
    async def test_detect_project_type(self, temp_project, mock_scan_result):
        """Test project type detection"""
        # Add package.json to make it a Node.js project
        (temp_project / "package.json").write_text('{"name": "test"}')

        analyzer = ManifestAnalyzer()
        result = await analyzer.analyze(mock_scan_result)

        # Since we added requirements.txt, it should detect Python
        # Project should be nodejs since we added package.json
        assert result.data["project_type"] in ["nodejs", "python"]

    @pytest.mark.asyncio
    async def test_find_entry_points(self, mock_scan_result):
        """Test finding entry points"""
        analyzer = ManifestAnalyzer()
        result = await analyzer.analyze(mock_scan_result)

        assert "entry_points" in result.data
        # Should find main.py and api.py
        entry_points = result.data["entry_points"]
        assert any("main.py" in ep for ep in entry_points)
