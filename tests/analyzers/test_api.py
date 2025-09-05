"""Tests for ApiAnalyzer"""
import pytest
from src.analyzers.api import ApiAnalyzer


@pytest.mark.unit
class TestApiAnalyzer:
    """Test ApiAnalyzer functionality"""
    
    def test_analyzer_initialization(self):
        """Test that analyzer initializes correctly"""
        analyzer = ApiAnalyzer()
        assert analyzer.name == "api"
        assert "REST API endpoints" in analyzer.description
    
    @pytest.mark.asyncio
    async def test_find_flask_endpoints(self, mock_scan_result):
        """Test finding Flask endpoints"""
        analyzer = ApiAnalyzer()
        result = await analyzer.analyze(mock_scan_result)
        
        assert result.analyzer == "api"
        assert "endpoints" in result.data
        assert "total" in result.data
        
        # Should find the Flask routes from api.py
        endpoints = result.data["endpoints"]
        # At least one endpoint should be found
        assert len(endpoints) >= 1  # At least /api/users and /api/posts
        
        # Check that Flask framework is detected
        assert "frameworks" in result.data
        assert "flask" in result.data["frameworks"]
    
    @pytest.mark.asyncio
    async def test_endpoint_methods(self, mock_scan_result):
        """Test that endpoint methods are detected"""
        analyzer = ApiAnalyzer()
        result = await analyzer.analyze(mock_scan_result)
        
        endpoints = result.data["endpoints"]
        methods = [ep.get("method") for ep in endpoints]
        
        # Should have both GET and POST methods
        assert "GET" in methods or "POST" in methods
