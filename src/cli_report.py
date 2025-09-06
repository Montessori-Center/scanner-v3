#!/usr/bin/env python3
"""Report generation command for Scanner v3"""
import json
from pathlib import Path

from src.output.markdown import MarkdownFormatter


def generate_report(json_file):
    """Generate markdown report from JSON scan results"""
    with open(json_file) as f:
        data = json.load(f)

    formatter = MarkdownFormatter()
    report = formatter.format(data)

    report_file = Path(json_file).stem + "_report.md"
    Path(report_file).write_text(report)
    return report_file
