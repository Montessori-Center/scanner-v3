from typing import Dict, Any
import json

class JSONFormatter:
    def format(self, results: Dict[str, Any]) -> str:
        return json.dumps(results, indent=2, default=str)
