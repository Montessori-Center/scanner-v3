#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LLM Context Builder for Scanner v3"""
from typing import Dict, Any, List
import json
from src.output.base import BaseFormatter


class LLMContextBuilder(BaseFormatter):
    """Build optimized context for Large Language Models"""
    
    def format(self, results: Dict[str, Any]) -> str:
        """Build LLM context from analysis results
        
        Args:
            results: Analysis results dictionary
            
        Returns:
            Optimized context string for LLM consumption
        """
        return self.build(results)
    
    def build(self, results: Dict[str, Any], max_tokens: int = 4000) -> str:
        """Build prioritized context for LLM
        
        Args:
            results: Analysis results
            max_tokens: Maximum tokens (approximate)
            
        Returns:
            Context string optimized for LLM understanding
        """
        context_parts = []
        
        # Priority 1: Project Overview
        manifest = results.get("analyzers", {}).get("manifest", {})
        if manifest:
            context_parts.append(self._format_overview(manifest))
        
        # Priority 2: Critical Issues
        security = results.get("analyzers", {}).get("security", {})
        if security:
            critical = self._format_critical_issues(security)
            if critical:
                context_parts.append(critical)
        
        # Priority 3: Architecture & Structure
        api = results.get("analyzers", {}).get("api", {})
        database = results.get("analyzers", {}).get("database", {})
        if api or database:
            context_parts.append(self._format_architecture(api, database))
        
        # Priority 4: Dependencies & Tech Stack
        deps = results.get("analyzers", {}).get("dependencies", {})
        if deps:
            context_parts.append(self._format_tech_stack(deps))
        
        # Priority 5: Technical Debt
        todos = results.get("analyzers", {}).get("todos", {})
        errors = results.get("analyzers", {}).get("errors", {})
        if todos or errors:
            context_parts.append(self._format_tech_debt(todos, errors))
        
        # Join and truncate to max_tokens (rough estimate: 1 token ≈ 4 chars)
        context = "\n\n".join(filter(None, context_parts))
        max_chars = max_tokens * 4
        
        if len(context) > max_chars:
            context = context[:max_chars] + "\n\n[Context truncated due to length]"
        
        return context
    
    def _format_overview(self, manifest: Dict) -> str:
        """Format project overview"""
        parts = [
            "PROJECT OVERVIEW:",
            f"Type: {manifest.get('project_type', 'unknown')}",
            f"Files: {manifest.get('total_files', 0):,}",
            f"Languages: {', '.join(manifest.get('languages', {}).keys())}"
        ]
        
        if manifest.get('entry_points'):
            parts.append(f"Entry Points: {', '.join(manifest['entry_points'][:5])}")
        
        return "\n".join(parts)
    
    def _format_critical_issues(self, security: Dict) -> str:
        """Format critical security issues"""
        critical = security.get("vulnerabilities", {}).get("critical", [])
        if not critical:
            return ""
        
        parts = [
            "CRITICAL SECURITY ISSUES:",
            f"Found {len(critical)} critical vulnerabilities that need immediate attention."
        ]
        
        # Show first 3 critical issues
        for issue in critical[:3]:
            parts.append(f"- {issue.get('type', 'Unknown')}: {issue.get('file', 'Unknown file')}")
        
        if len(critical) > 3:
            parts.append(f"... and {len(critical) - 3} more critical issues")
        
        return "\n".join(parts)
    
    def _format_architecture(self, api: Dict, database: Dict) -> str:
        """Format architecture information"""
        parts = ["ARCHITECTURE:"]
        
        if api and api.get("total", 0) > 0:
            parts.append(f"API: {api.get('total', 0)} endpoints")
            frameworks = api.get("frameworks", [])
            if frameworks:
                parts.append(f"Frameworks: {', '.join(frameworks)}")
        
        if database:
            db_type = database.get("database_type", "unknown")
            tables = database.get("statistics", {}).get("total_tables", 0)
            parts.append(f"Database: {db_type} with {tables} tables")
            
            if database.get("features", {}).get("has_migrations"):
                parts.append("Has database migrations")
        
        return "\n".join(parts)
    
    def _format_tech_stack(self, deps: Dict) -> str:
        """Format technology stack"""
        parts = [
            "TECHNOLOGY STACK:",
            f"Primary Language: {deps.get('primary_language', 'unknown')}",
            f"Total Dependencies: {deps.get('total', 0)}"
        ]
        
        # Show key dependencies per language
        for lang, packages in deps.get("dependencies", {}).items():
            if packages:
                key_deps = packages[:5]
                parts.append(f"{lang.title()}: {', '.join(key_deps)}")
                if len(packages) > 5:
                    parts.append(f"  ... and {len(packages) - 5} more")
        
        return "\n".join(parts)
    
    def _format_tech_debt(self, todos: Dict, errors: Dict) -> str:
        """Format technical debt information"""
        parts = ["TECHNICAL DEBT:"]
        
        if todos:
            total_todos = todos.get("total", 0)
            high_priority = todos.get("by_priority", {}).get("high", 0)
            parts.append(f"TODOs: {total_todos} total, {high_priority} high priority")
            
            # Show distribution
            by_type = todos.get("by_type", {})
            if by_type:
                todo_summary = []
                for todo_type, count in list(by_type.items())[:5]:
                    if count > 0:
                        todo_summary.append(f"{todo_type}:{count}")
                if todo_summary:
                    parts.append(f"Types: {', '.join(todo_summary)}")
        
        if errors:
            error_types = errors.get("error_types", {})
            if error_types:
                critical = error_types.get("critical", 0)
                if critical > 0:
                    parts.append(f"Critical Errors: {critical} found in logs")
        
        return "\n".join(parts)
