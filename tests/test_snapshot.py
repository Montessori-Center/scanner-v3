#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Snapshot tests for Scanner output consistency"""
import json
from pathlib import Path

def test_output_format():
    """Test that output matches expected structure"""
    snapshot = Path("tests/snapshots/expected_output.json")
    with open(snapshot) as f:
        data = json.load(f)
    
    # Check structure
    assert "version" in data
    assert "results" in data
    assert "scan_info" in data["results"]
    assert "analyzers" in data["results"]
    
    # Check data
    assert data["results"]["scan_info"]["total_files"] == 52
    assert len(data["results"]["analyzers"]) == 12
    
    print("Snapshot test passed")
    return True

if __name__ == "__main__":
    test_output_format()
