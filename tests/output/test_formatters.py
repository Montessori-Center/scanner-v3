"""Tests for output formatters"""
import pytest
import json
from src.output.markdown import MarkdownFormatter
from src.output.json import JSONFormatter
from src.output.context import LLMContextBuilder


@pytest.mark.unit
class TestFormatters:
    """Test output formatters"""
    
    @pytest.fixture
    def sample_results(self):
        """Sample analysis results for testing"""
        return {
            "scan_info": {
                "path": "/test/project",
                "total_files": 100,
                "total_size": 1048576,
                "duration": 2.5
            },
            "analyzers": {
                "manifest": {
                    "project_type": "python",
                    "total_files": 100,
                    "languages": {"python": 80, "javascript": 20}
                },
                "api": {
                    "total": 10,
                    "endpoints": [
                        {"method": "GET", "path": "/api/users", "framework": "flask"},
                        {"method": "POST", "path": "/api/posts", "framework": "flask"}
                    ],
                    "frameworks": ["flask"]
                },
                "security": {
                    "total": 5,
                    "vulnerabilities": {
                        "critical": [{"type": "sql_injection", "file": "test.py"}],
                        "high": [],
                        "medium": [],
                        "low": []
                    }
                },
                "todos": {
                    "total": 15,
                    "by_type": {"TODO": 10, "FIXME": 5},
                    "by_priority": {"high": 5, "medium": 10, "low": 0}
                }
            }
        }
    
    def test_markdown_formatter(self, sample_results):
        """Test MarkdownFormatter"""
        formatter = MarkdownFormatter()
        output = formatter.format(sample_results)
        
        assert isinstance(output, str)
        assert "# Scanner v3 Analysis Report" in output
        assert "Total Files" in output
        assert "API Endpoints" in output
        assert "Security" in output
        assert "python" in output.lower()
    
    def test_json_formatter(self, sample_results):
        """Test JSONFormatter"""
        formatter = JSONFormatter()
        output = formatter.format(sample_results)
        
        assert isinstance(output, str)
        parsed = json.loads(output)  # Should be valid JSON
        assert "version" in parsed
        assert "generated" in parsed
        assert "results" in parsed
        assert parsed["results"]["scan_info"]["total_files"] == 100
    
    def test_llm_context_builder(self, sample_results):
        """Test LLMContextBuilder"""
        builder = LLMContextBuilder()
        output = builder.format(sample_results)
        
        assert isinstance(output, str)
        assert "PROJECT OVERVIEW" in output
        assert "Type: python" in output
        assert len(output) <= 16000  # Max 4000 tokens * 4 chars
        
        # Test with security issues
        assert "CRITICAL SECURITY ISSUES" in output
        assert "sql_injection" in output
    
    def test_llm_context_truncation(self, sample_results):
        """Test that LLM context truncates properly"""
        builder = LLMContextBuilder()
        
        # Create huge results
        huge_results = sample_results.copy()
        huge_results["analyzers"]["api"]["endpoints"] = [
            {"method": "GET", "path": f"/api/endpoint{i}", "framework": "flask"}
            for i in range(1000)
        ]
        
        output = builder.build(huge_results, max_tokens=100)
        assert len(output) <= 400  # 100 tokens * 4 chars
        assert "[Context truncated due to length]" in output or len(output) < 400
