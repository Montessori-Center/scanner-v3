#!/usr/bin/env python3
"""JSON formatter for Scanner v3 results"""
import json
from datetime import datetime
from typing import Any, Dict

from src.output.base import BaseFormatter


class JSONFormatter(BaseFormatter):
    """Format analysis results as JSON"""

    def format(self, results: Dict[str, Any]) -> str:
        """Format results as JSON

        Args:
            results: Analysis results dictionary

        Returns:
            JSON formatted string with indentation
        """
        # Add metadata
        output = {
            "version": "3.0.0",
            "generated": datetime.now().isoformat(),
            "results": results
        }

        # Pretty print with custom encoder for datetime objects
        return json.dumps(output, indent=2, default=self._json_encoder, ensure_ascii=False)

    def _json_encoder(self, obj):
        """Custom JSON encoder for special types"""
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
