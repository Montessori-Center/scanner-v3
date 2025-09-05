"""API endpoints analyzer"""
import re
import json
import yaml
from typing import List, Dict
from pathlib import Path

from src.core.base import BaseAnalyzer

from src.core.logger import get_logger
from src.core.models import ScanResult, AnalysisResult


class ApiAnalyzer(BaseAnalyzer):
    """Find and analyze API endpoints in the project"""
    

    logger = get_logger("api")
    name = "api"
    description = "Extract REST API endpoints, GraphQL schemas, WebSocket routes"

    logger = get_logger("api")
    
    # Framework-specific patterns
    PATTERNS = {
        # FastAPI/Starlette
        'fastapi': [
            r'@app\.(get|post|put|delete|patch|options|head)\(["\']([^"\']+)',
            r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)',
        ],
        # Flask
        'flask': [
            r'@app\.route\(["\']([^"\']+).*methods=\[([^\]]+)',
            r'@blueprint\.route\(["\']([^"\']+)',
        ],
        # Express.js
        'express': [
            r'app\.(get|post|put|delete|patch|use)\(["\']([^"\']+)',
            r'router\.(get|post|put|delete|patch)\(["\']([^"\']+)',
        ],
        # Django
        'django': [
            r'path\(["\']([^"\']+)["\']',
            r'url\(r?\^([^$]+)\$',
        ],
        # Laravel/PHP
        'laravel': [
            r'Route::(get|post|put|delete|patch)\(["\']([^"\']+)',
            r'\$router->(get|post|put|delete|patch)\(["\']([^"\']+)',
        ],
        # Spring Boot
        'spring': [
            r'@(?:Get|Post|Put|Delete|Patch)Mapping\(["\']([^"\']+)',
            r'@RequestMapping.*value\s*=\s*["\']([^"\']+)',
        ]
    }
    
    async def analyze(self, scan: ScanResult) -> AnalysisResult:
        """Analyze API endpoints"""
        
        endpoints = []
        openapi_files = []
        graphql_files = []
        frameworks_detected = set()
        
        for file in scan.files:
            file_path = file.path
            
            # Check for OpenAPI/Swagger files
            if file.name in ['openapi.json', 'openapi.yaml', 'swagger.json', 'swagger.yaml']:
                openapi_files.append(file.name)
                try:
                    endpoints.extend(self._parse_openapi(file_path))
                except Exception as e:
                    self.logger.debug(f"Error in OpenAPI parsing: {e}")
            
            # Check for GraphQL schemas
            elif file.suffix in ['.graphql', '.gql'] or file.name == 'schema.graphql':
                graphql_files.append(file.name)
            
            # Parse source code for endpoints
            elif file.suffix in ['.py', '.js', '.ts', '.php', '.java', '.rb']:
                try:
                    content = file.read_text(errors='ignore')[:200000]  # First 200KB
                    
                    # Try all patterns
                    for framework, patterns in self.PATTERNS.items():
                        for pattern in patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                frameworks_detected.add(framework)
                                for match in matches[:10]:  # Max 10 per file
                                    if isinstance(match, tuple):
                                        if len(match) == 2:
                                            method, path = match
                                        else:
                                            path = match[0]
                                            method = 'GET'
                                    else:
                                        path = match
                                        method = 'GET'
                                    
                                    endpoints.append({
                                        'method': method.upper() if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] else 'GET',
                                        'path': path,
                                        'file': str(file.path.relative_to(scan.root)),
                                        'framework': framework
                                    })
                except Exception as e:
                    self.logger.debug(f"Error in endpoint extraction: {e}")
        
        # Deduplicate endpoints
        unique_endpoints = []
        seen = set()
        for ep in endpoints[:200]:  # Max 200 endpoints
            key = f"{ep.get('method', 'GET')}:{ep.get('path', '')}"
            if key not in seen:
                seen.add(key)
                unique_endpoints.append(ep)
        
        # Count by method
        method_counts = {}
        for ep in unique_endpoints:
            method = ep.get('method', 'GET')
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return AnalysisResult(
            analyzer=self.name,
            data={
                "endpoints": unique_endpoints[:100],  # Top 100
                "total": len(unique_endpoints),
                "by_method": method_counts,
                "frameworks": list(frameworks_detected),
                "has_openapi": len(openapi_files) > 0,
                "has_graphql": len(graphql_files) > 0,
                "openapi_files": openapi_files,
                "graphql_files": graphql_files[:5]
            }
        )
    
    def _parse_openapi(self, file_path: Path) -> List[Dict]:
        """Parse OpenAPI specification file"""
        endpoints = []
        
        try:
            with open(file_path) as f:
                if file_path.suffix == '.json':
                    spec = json.load(f)
                else:
                    spec = yaml.safe_load(f)
                
                if spec and 'paths' in spec:
                    for path, methods in spec['paths'].items():
                        for method in methods:
                            if method in ['get', 'post', 'put', 'delete', 'patch']:
                                endpoints.append({
                                    'method': method.upper(),
                                    'path': path,
                                    'file': file_path.name,
                                    'framework': 'openapi'
                                })
        except Exception as e:
            self.logger.debug(f"Error in OpenAPI specification parsing: {e}")
        
        return endpoints
