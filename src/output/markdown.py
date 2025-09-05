"""Markdown formatter for Scanner v3 results"""
from typing import Dict, Any, List
from datetime import datetime
from src.output.base import BaseFormatter


class MarkdownFormatter(BaseFormatter):
    """Format analysis results as Markdown documentation"""
    
    def format(self, results: Dict[str, Any]) -> str:
        """Format results as Markdown
        
        Args:
            results: Analysis results dictionary containing:
                - scan_info: scanning metadata
                - analyzers: results from each analyzer
                
        Returns:
            Markdown formatted string
        """
        lines = []
        
        # Header
        lines.append("# Scanner v3 Analysis Report")
        lines.append("")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Scan Summary
        if "scan_info" in results:
            lines.append("## 📊 Scan Summary")
            lines.append("")
            info = results["scan_info"]
            lines.append(f"- **Project Path**: `{info.get('path', 'Unknown')}`")
            lines.append(f"- **Total Files**: {info.get('total_files', 0):,}")
            lines.append(f"- **Total Size**: {self._format_size(info.get('total_size', 0))}")
            lines.append(f"- **Scan Duration**: {info.get('duration', 0):.2f} seconds")
            lines.append("")
        
        # Analyzer Results
        if "analyzers" in results:
            lines.append("## 🔍 Analysis Results")
            lines.append("")
            
            for analyzer_name, data in sorted(results["analyzers"].items()):
                lines.append(f"### {self._format_analyzer_name(analyzer_name)}")
                lines.append("")
                
                if isinstance(data, dict):
                    lines.extend(self._format_analyzer_data(analyzer_name, data))
                else:
                    lines.append(f"```\n{data}\n```")
                lines.append("")
        
        return "\n".join(lines)
    
    def _format_analyzer_name(self, name: str) -> str:
        """Format analyzer name with emoji"""
        emojis = {
            "api": "🌐 API Endpoints",
            "database": "🗄️ Database",
            "dependencies": "📦 Dependencies",
            "docker": "🐳 Docker",
            "env": "🔐 Environment Variables",
            "errors": "❌ Errors & Logs",
            "functions": "🔧 Functions & Classes",
            "git": "📚 Git Repository",
            "manifest": "📁 Project Structure",
            "security": "🔒 Security",
            "todos": "📝 TODOs & Technical Debt",
            "webhooks": "🔗 Webhooks & Integrations"
        }
        return emojis.get(name, f"📋 {name.title()}")
    
    def _format_analyzer_data(self, name: str, data: Dict[str, Any]) -> List[str]:
        """Format specific analyzer data"""
        lines = []
        
        if name == "api" and "endpoints" in data:
            lines.append(f"**Total Endpoints**: {data.get('total', 0)}")
            lines.append("")
            if data.get("endpoints"):
                lines.append("| Method | Path | Framework |")
                lines.append("|--------|------|-----------|")
                for ep in data["endpoints"][:20]:  # Top 20
                    lines.append(f"| {ep.get('method', 'GET')} | `{ep.get('path', '')}` | {ep.get('framework', '')} |")
            
        elif name == "dependencies" and "dependencies" in data:
            lines.append(f"**Total Dependencies**: {data.get('total', 0)}")
            lines.append(f"**Primary Language**: {data.get('primary_language', 'unknown')}")
            lines.append("")
            for lang, deps in data.get("dependencies", {}).items():
                if deps:
                    lines.append(f"**{lang.title()}** ({len(deps)}): `{', '.join(deps[:10])}`")
        
        elif name == "security" and "vulnerabilities" in data:
            vulns = data.get("vulnerabilities", {})
            lines.append(f"**Total Issues**: {data.get('total', 0)}")
            lines.append("")
            lines.append("| Severity | Count |")
            lines.append("|----------|-------|")
            lines.append(f"| 🔴 Critical | {len(vulns.get('critical', []))} |")
            lines.append(f"| 🟠 High | {len(vulns.get('high', []))} |")
            lines.append(f"| 🟡 Medium | {len(vulns.get('medium', []))} |")
            lines.append(f"| 🟢 Low | {len(vulns.get('low', []))} |")
            
        elif name == "todos" and "todos" in data:
            lines.append(f"**Total TODOs**: {data.get('total', 0)}")
            lines.append("")
            by_type = data.get("by_type", {})
            if by_type:
                lines.append("| Type | Count |")
                lines.append("|------|-------|")
                for todo_type, count in by_type.items():
                    if count > 0:
                        lines.append(f"| {todo_type} | {count} |")
        
        elif name == "env" and "variables" in data:
            lines.append(f"**Total Variables**: {data.get('count', 0)}")
            stats = data.get("stats", {})
            if stats:
                lines.append(f"**From Files**: {stats.get('from_files', 0)}")
                lines.append(f"**From Code**: {stats.get('from_code', 0)}")
                lines.append(f"**Sensitive**: {stats.get('sensitive', 0)}")
        
        elif name == "git":
            lines.append(f"**Current Branch**: {data.get('current_branch', 'unknown')}")
            stats = data.get("stats", {})
            if stats:
                lines.append(f"**Total Commits**: {stats.get('total_commits', 0):,}")
                lines.append(f"**Contributors**: {stats.get('total_contributors', 0)}")
                lines.append(f"**Branches**: {stats.get('total_branches', 0)}")
        
        elif name == "manifest":
            lines.append(f"**Project Type**: {data.get('project_type', 'unknown')}")
            lines.append(f"**Has Tests**: {'✅' if data.get('has_tests') else '❌'}")
            lines.append(f"**Has Documentation**: {'✅' if data.get('has_docs') else '❌'}")
            lines.append(f"**Has CI/CD**: {'✅' if data.get('has_ci') else '❌'}")
            
        else:
            # Generic formatting for other analyzers
            for key, value in data.items():
                if key not in ["errors", "warnings"] and not key.startswith("_"):
                    if isinstance(value, (list, dict)) and len(str(value)) > 100:
                        lines.append(f"**{key.replace('_', ' ').title()}**: {len(value)} items")
                    else:
                        lines.append(f"**{key.replace('_', ' ').title()}**: {value}")
        
        return lines
    
    def _format_size(self, bytes_size: int) -> str:
        """Format bytes to human readable size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"
