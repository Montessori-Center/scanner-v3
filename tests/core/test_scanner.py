#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Scanner"""
import pytest
from pathlib import Path
from src.core.scanner import Scanner
from src.core.config import Settings


@pytest.mark.unit
class TestScanner:
    """Test Scanner functionality"""
    
    def test_scanner_initialization(self):
        """Test scanner initialization"""
        settings = Settings()
        scanner = Scanner(settings)
        assert scanner.settings == settings
    
    @pytest.mark.asyncio
    async def test_scan_project(self, temp_project):
        """Test scanning a project"""
        settings = Settings(profile="fast")
        scanner = Scanner(settings)
        
        result = await scanner.scan(temp_project)
        
        assert result.root == temp_project
        assert result.total_files > 0
        assert result.duration >= 0
        assert len(result.files) == result.total_files
    
    @pytest.mark.asyncio
    async def test_file_exclusion(self, temp_project):
        """Test that excluded files are not scanned"""
        # Create a node_modules directory
        (temp_project / "node_modules").mkdir()
        (temp_project / "node_modules" / "test.js").write_text("test")
        
        settings = Settings()
        scanner = Scanner(settings)
        result = await scanner.scan(temp_project)
        
        # node_modules should be excluded
        node_files = [f for f in result.files if "node_modules" in str(f.path)]
        assert len(node_files) == 0
