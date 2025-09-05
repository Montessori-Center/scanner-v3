"""Environment variables analyzer"""
import re
from typing import Dict, List
from pathlib import Path
from dotenv import dotenv_values
import yaml
import json


from src.core.logger import get_logger
from src.core.base import BaseAnalyzer
from src.core.models import ScanResult, AnalysisResult


class EnvAnalyzer(BaseAnalyzer):
    """Find and analyze environment variables from all sources"""
    

    logger = get_logger("env")
    name = "env"
    description = "Environment variables from .env, docker-compose, k8s configs"
    
    async def analyze(self, scan: ScanResult) -> AnalysisResult:
        """Analyze environment variables"""
        
        env_vars = {}
        sources = []
        from_code = []
        
        for file in scan.files:
            file_path = file.path
            
            # 1. .env files
            if file.name.startswith('.env'):
                try:
                    vars = dotenv_values(file_path)
                    env_vars.update(vars)
                    sources.append(f".env file: {file.name}")
                except Exception as e:
                    self.logger.debug(f"Error in .env file parsing: {e}")
            
            # 2. docker-compose.yml
            elif file.name in ['docker-compose.yml', 'docker-compose.yaml']:
                try:
                    with open(file_path) as f:
                        compose = yaml.safe_load(f)
                        if compose and 'services' in compose:
                            for service, config in compose.get('services', {}).items():
                                if 'environment' in config:
                                    env = config['environment']
                                    if isinstance(env, dict):
                                        env_vars.update(env)
                                        sources.append(f"docker-compose: {service}")
                                    elif isinstance(env, list):
                                        # Handle list format: ["KEY=value", "KEY2=value2"]
                                        for var in env:
                                            if '=' in var:
                                                key, value = var.split('=', 1)
                                                env_vars[key] = value
                                        sources.append(f"docker-compose: {service}")
                except Exception as e:
                    self.logger.debug(f"Error in docker-compose.yml parsing: {e}")
            
            # 3. Find env vars referenced in code
            elif file.suffix in ['.py', '.js', '.ts', '.php']:
                try:
                    content = file.read_text(errors='ignore')[:100000]  # First 100KB
                    
                    # Python: os.getenv('VAR'), os.environ['VAR']
                    python_vars = re.findall(r'os\.(?:getenv|environ)\[?["\']([A-Z_][A-Z0-9_]*)', content)
                    
                    # JS/TS: process.env.VAR
                    js_vars = re.findall(r'process\.env\.([A-Z_][A-Z0-9_]*)', content)
                    
                    # PHP: $_ENV['VAR'], getenv('VAR')
                    php_vars = re.findall(r'(?:\$_ENV\[|getenv\()["\']([A-Z_][A-Z0-9_]*)', content)
                    
                    for var in python_vars + js_vars + php_vars:
                        if var and var not in env_vars:
                            from_code.append(var)
                            env_vars[var] = "***REFERENCED_IN_CODE***"
                except Exception as e:
                    self.logger.debug(f"Error in code environment variable extraction: {e}")
        
        # Mask sensitive values
        masked_vars = {}
        sensitive_patterns = ['PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'API', 'PRIVATE']
        
        for key, value in env_vars.items():
            if any(pattern in key.upper() for pattern in sensitive_patterns):
                masked_vars[key] = "***REDACTED***" if value != "***REFERENCED_IN_CODE***" else value
            else:
                masked_vars[key] = value
        
        return AnalysisResult(
            analyzer=self.name,
            data={
                "variables": masked_vars,
                "count": len(env_vars),
                "sources": list(set(sources))[:10],
                "from_code": list(set(from_code))[:20],
                "stats": {
                    "total": len(env_vars),
                    "from_files": len([k for k, v in env_vars.items() if v != "***REFERENCED_IN_CODE***"]),
                    "from_code": len(from_code),
                    "sensitive": len([k for k in masked_vars if masked_vars[k] == "***REDACTED***"])
                }
            }
        )
