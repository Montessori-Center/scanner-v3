#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Errors and Logs Analyzer"""
import re
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter
from src.core.base import BaseAnalyzer
from src.core.models import ScanResult, AnalysisResult

from src.core.logger import get_logger

class ErrorsAnalyzer(BaseAnalyzer):
    """Analyze error logs and patterns"""
    
    name = "errors"
    description = "Extract errors from logs and code"

    logger = get_logger("errors")
    
    ERROR_PATTERNS = {
        'exception': r'(?i)(exception|error|traceback|stack trace)',
        'critical': r'(?i)(critical|fatal|emergency|panic)',
        'warning': r'(?i)(warning|warn|deprecated)',
        'failed': r'(?i)(failed|failure|error|cannot|unable)',
        'null_ref': r'(?i)(null|undefined|none).*(?:reference|pointer|error)',
        'timeout': r'(?i)(timeout|timed out|deadline)',
        'memory': r'(?i)(out of memory|oom|memory leak|heap)',
        'permission': r'(?i)(permission denied|access denied|forbidden|401|403)',
    }
    
    async def analyze(self, scan_result: ScanResult) -> AnalysisResult:
        """Analyze errors and logs"""
        errors = []
        error_types = Counter()
        
        # Check log files and common error locations
        for file_info in scan_result.files[:100]:
            if any(pattern in str(file_info.path).lower() 
                   for pattern in ['log', 'error', 'debug', 'exception']):
                try:
                    content = file_info.path.read_text(errors='ignore')
                    lines = content.split('\n')[:500]  # First 500 lines
                    
                    for line_no, line in enumerate(lines, 1):
                        for error_type, pattern in self.ERROR_PATTERNS.items():
                            if re.search(pattern, line):
                                error_types[error_type] += 1
                                errors.append({
                                    'type': error_type,
                                    'file': str(file_info.path.name),
                                    'line': line_no,
                                    'text': line[:200]
                                })
                                if len(errors) >= 50:
                                    break
                except Exception:
                    continue
                    
        # Check source code for error handling
        error_handling = self._check_error_handling(scan_result)
        
        return AnalysisResult(
            analyzer=self.name,
            data={
                "errors": errors[:30],
                "error_types": dict(error_types),
                "total_errors": len(errors),
                "has_logging": self._check_logging(scan_result),
                "error_handling": error_handling,
                "critical_count": error_types.get('critical', 0),
                "warning_count": error_types.get('warning', 0)
            }
        )
    
    def _check_error_handling(self, scan_result: ScanResult) -> Dict:
        """Check error handling patterns"""
        patterns = {
            'try_catch': 0,
            'error_callbacks': 0,
            'logging': 0
        }
        
        for file_info in scan_result.files[:50]:
            if file_info.extension in ['.py', '.js', '.ts', '.java']:
                try:
                    content = file_info.path.read_text(errors='ignore')
                    patterns['try_catch'] += len(re.findall(r'\btry\b|\bcatch\b|\bexcept\b', content))
                    patterns['error_callbacks'] += len(re.findall(r'on_?error|error_?handler|catch', content, re.I))
                    patterns['logging'] += len(re.findall(r'log\.|logger\.|console\.', content))
                except Exception as e:
                    self.logger.debug(f"Error analyzing errors in file: {e}")
                    
        return patterns
    
    def _check_logging(self, scan_result: ScanResult) -> bool:
        """Check if project has logging configured"""
        for file_info in scan_result.files:
            name = file_info.path.name.lower()
            if any(x in name for x in ['logging', 'log4', 'winston', 'bunyan', 'pino']):
                return True
        return False
