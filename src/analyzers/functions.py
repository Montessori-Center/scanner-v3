#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Functions and Classes Analyzer"""
import ast
import re
from pathlib import Path
from typing import Dict, List, Any
from src.core.base import BaseAnalyzer

from src.core.logger import get_logger
from src.core.models import ScanResult, AnalysisResult

class FunctionsAnalyzer(BaseAnalyzer):
    """Extract functions, classes, and methods"""
    
    name = "functions"
    description = "Extract function signatures and documentation"

    logger = get_logger("functions")
    
    async def analyze(self, scan_result: ScanResult) -> AnalysisResult:
        """Analyze functions and classes"""
        functions = []
        classes = []
        
        for file_info in scan_result.files[:50]:
            if file_info.extension == '.py':
                funcs, cls = self._analyze_python(file_info.path)
                functions.extend(funcs)
                classes.extend(cls)
            elif file_info.extension in ['.js', '.ts']:
                funcs = self._analyze_javascript(file_info.path)
                functions.extend(funcs)
                
        return AnalysisResult(
            analyzer=self.name,
            data={
                "functions": functions[:100],
                "classes": classes[:50],
                "total_functions": len(functions),
                "total_classes": len(classes),
                "average_function_size": self._calculate_avg_size(functions),
                "has_docstrings": self._check_documentation(functions)
            }
        )
    
    def _analyze_python(self, file_path: Path) -> tuple:
        """Extract Python functions and classes using AST"""
        functions = []
        classes = []
        
        try:
            content = file_path.read_text(errors='ignore')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        'name': node.name,
                        'file': file_path.name,
                        'args': [arg.arg for arg in node.args.args],
                        'has_doc': ast.get_docstring(node) is not None,
                        'is_async': isinstance(node, ast.AsyncFunctionDef)
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        'name': node.name,
                        'file': file_path.name,
                        'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                        'has_doc': ast.get_docstring(node) is not None
                    })
        except Exception as e:
            self.logger.debug(f"Error analyzing Python file: {e}")
            
        return functions[:20], classes[:10]
    
    def _analyze_javascript(self, file_path: Path) -> List:
        """Extract JavaScript functions using regex"""
        functions = []
        
        try:
            content = file_path.read_text(errors='ignore')
            
            # Function declarations
            for match in re.finditer(r'function\s+(\w+)\s*\((.*?)\)', content):
                functions.append({
                    'name': match.group(1),
                    'file': file_path.name,
                    'args': [a.strip() for a in match.group(2).split(',') if a.strip()],
                    'type': 'function'
                })
            
            # Arrow functions
            for match in re.finditer(r'const\s+(\w+)\s*=\s*\((.*?)\)\s*=>', content):
                functions.append({
                    'name': match.group(1),
                    'file': file_path.name,
                    'args': [a.strip() for a in match.group(2).split(',') if a.strip()],
                    'type': 'arrow'
                })
                
        except Exception as e:
            self.logger.debug(f"Error analyzing JavaScript file: {e}")
            
        return functions[:20]
    
    def _calculate_avg_size(self, functions: List) -> int:
        """Calculate average function size"""
        if not functions:
            return 0
        return len(functions) // max(len(set(f['file'] for f in functions)), 1)
    
    def _check_documentation(self, functions: List) -> float:
        """Check documentation percentage"""
        if not functions:
            return 0.0
        with_docs = sum(1 for f in functions if f.get('has_doc', False))
        return round(with_docs / len(functions) * 100, 2)
