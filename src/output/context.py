from typing import Dict, Any
import json

class LLMContextBuilder:
    def build(self, results: Dict[str, Any], max_tokens: int = 4000) -> str:
        context = {
            "project_type": results.get("manifest", {}).get("project_type"),
            "total_files": results.get("manifest", {}).get("total_files"),
            "languages": results.get("manifest", {}).get("languages"),
            "api_endpoints": results.get("api", {}).get("total", 0),
            "dependencies": results.get("dependencies", {}).get("total", 0),
            "security_critical": len(results.get("security", {}).get("vulnerabilities", {}).get("critical", [])),
            "todos_high": results.get("todos", {}).get("by_priority", {}).get("high", 0)
        }
        return json.dumps(context, indent=2)[:max_tokens * 4]
