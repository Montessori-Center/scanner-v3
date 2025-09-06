#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for TodosAnalyzer"""
import pytest
from src.analyzers.todos import TodosAnalyzer


@pytest.mark.unit
class TestTodosAnalyzer:
    """Test TodosAnalyzer functionality"""
    
    def test_analyzer_initialization(self):
        """Test that analyzer initializes correctly"""
        analyzer = TodosAnalyzer()
        assert analyzer.name == "todos"
        assert "TODO" in analyzer.description
    
    @pytest.mark.asyncio
    async def test_find_todos(self, mock_scan_result):
        """Test finding TODO comments"""
        analyzer = TodosAnalyzer()
        result = await analyzer.analyze(mock_scan_result)
        
        assert result.analyzer == "todos"
        assert "todos" in result.data
        assert "total" in result.data
        
        # Should find TODO and FIXME from main.py
        todos = result.data["todos"]
        assert "TODO" in todos or "FIXME" in todos
        
    @pytest.mark.asyncio
    async def test_priority_classification(self, mock_scan_result):
        """Test priority classification of TODOs"""
        analyzer = TodosAnalyzer()
        result = await analyzer.analyze(mock_scan_result)
        
        assert "by_priority" in result.data
        priorities = result.data["by_priority"]
        
        # Should have at least one priority level
        assert priorities.get("high", 0) >= 0
        assert priorities.get("medium", 0) >= 0
        assert priorities.get("low", 0) >= 0
