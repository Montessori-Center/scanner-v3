from typing import Dict, Any
import json

class MarkdownFormatter:
    def format(self, results: Dict[str, Any]) -> str:
        md = ["# Scanner Analysis Results\n\n"]
        for analyzer, data in results.items():
            md.append(f"## {analyzer.title()}\n")
            if isinstance(data, dict):
                for key, value in data.items():
                    if key != "data" and not key.startswith("_"):
                        md.append(f"- **{key}**: {value}\n")
            md.append("\n")
        return "".join(md)
