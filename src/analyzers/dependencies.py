"""Dependencies analyzer for all languages"""
import json
import yaml
import tomllib
from pathlib import Path
from typing import Dict, List

from src.core.base import BaseAnalyzer

from src.core.logger import get_logger
from src.core.models import ScanResult, AnalysisResult


class DependenciesAnalyzer(BaseAnalyzer):
    """Analyze project dependencies from various package managers"""
    
    name = "dependencies"
    description = "Extract dependencies from package.json, requirements.txt, etc."

    logger = get_logger("dependencies")
    
    async def analyze(self, scan: ScanResult) -> AnalysisResult:
        """Analyze project dependencies"""
        
        dependencies = {
            'python': [],
            'javascript': [],
            'php': [],
            'ruby': [],
            'go': [],
            'java': [],
            'rust': []
        }
        
        lockfiles = []
        package_managers = []
        
        for file in scan.files:
            file_path = file.path
            
            # Python
            if file.name == 'requirements.txt':
                try:
                    with open(file_path) as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                pkg = line.split('==')[0].split('>=')[0].split('~=')[0]
                                dependencies['python'].append(pkg)
                    package_managers.append('pip')
                except Exception as e:
                    self.logger.debug(f"Error parsing requirements.txt parsing: {e}")
            
            elif file.name == 'Pipfile':
                try:
                    with open(file_path) as f:
                        content = f.read()
                        # Simple Pipfile parsing
                        in_packages = False
                        for line in content.split('\n'):
                            if '[packages]' in line:
                                in_packages = True
                            elif '[' in line:
                                in_packages = False
                            elif in_packages and '=' in line:
                                pkg = line.split('=')[0].strip()
                                if pkg:
                                    dependencies['python'].append(pkg)
                    package_managers.append('pipenv')
                except Exception as e:
                    self.logger.debug(f"Error parsing Pipfile parsing: {e}")
            
            elif file.name == 'pyproject.toml':
                try:
                    with open(file_path, 'rb') as f:
                        data = tomllib.load(f)
                        # Poetry dependencies
                        if 'tool' in data and 'poetry' in data['tool']:
                            deps = data['tool']['poetry'].get('dependencies', {})
                            dependencies['python'].extend([k for k in deps.keys() if k != 'python'])
                            package_managers.append('poetry')
                        # Standard project dependencies
                        elif 'project' in data:
                            deps = data['project'].get('dependencies', [])
                            dependencies['python'].extend(deps)
                except Exception as e:
                    self.logger.debug(f"Error parsing pyproject.toml parsing: {e}")
            
            # JavaScript/Node
            elif file.name == 'package.json':
                try:
                    with open(file_path) as f:
                        pkg = json.load(f)
                        if 'dependencies' in pkg:
                            dependencies['javascript'].extend(pkg['dependencies'].keys())
                        if 'devDependencies' in pkg:
                            dependencies['javascript'].extend(pkg['devDependencies'].keys())
                    package_managers.append('npm')
                except Exception as e:
                    self.logger.debug(f"Error parsing package.json parsing: {e}")
            
            # PHP
            elif file.name == 'composer.json':
                try:
                    with open(file_path) as f:
                        composer = json.load(f)
                        if 'require' in composer:
                            for pkg in composer['require'].keys():
                                if not pkg.startswith('php') and not pkg.startswith('ext-'):
                                    dependencies['php'].append(pkg)
                    package_managers.append('composer')
                except Exception as e:
                    self.logger.debug(f"Error parsing composer.json parsing: {e}")
            
            # Ruby
            elif file.name == 'Gemfile':
                try:
                    with open(file_path) as f:
                        for line in f:
                            if line.strip().startswith('gem '):
                                # Extract gem name
                                parts = line.split("'")
                                if len(parts) >= 2:
                                    dependencies['ruby'].append(parts[1])
                                else:
                                    parts = line.split('"')
                                    if len(parts) >= 2:
                                        dependencies['ruby'].append(parts[1])
                    package_managers.append('bundler')
                except Exception as e:
                    self.logger.debug(f"Error parsing Gemfile parsing: {e}")
            
            # Go
            elif file.name == 'go.mod':
                try:
                    with open(file_path) as f:
                        for line in f:
                            if line.strip().startswith('require '):
                                parts = line.split()
                                if len(parts) >= 2:
                                    dependencies['go'].append(parts[1])
                    package_managers.append('go modules')
                except Exception as e:
                    self.logger.debug(f"Error parsing go.mod parsing: {e}")
            
            # Rust
            elif file.name == 'Cargo.toml':
                try:
                    with open(file_path, 'rb') as f:
                        data = tomllib.load(f)
                        deps = data.get('dependencies', {})
                        dependencies['rust'].extend(deps.keys())
                    package_managers.append('cargo')
                except Exception as e:
                    self.logger.debug(f"Error parsing Cargo.toml parsing: {e}")
            
            # Lock files
            elif file.name in ['package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 
                             'composer.lock', 'Pipfile.lock', 'poetry.lock', 
                             'Gemfile.lock', 'Cargo.lock']:
                lockfiles.append(file.name)
        
        # Count total and find primary language
        total = sum(len(deps) for deps in dependencies.values())
        primary_language = max(dependencies.keys(), key=lambda k: len(dependencies[k])) if total > 0 else 'unknown'
        
        return AnalysisResult(
            analyzer=self.name,
            data={
                "dependencies": dependencies,
                "total": total,
                "primary_language": primary_language,
                "package_managers": list(set(package_managers)),
                "has_lockfiles": len(lockfiles) > 0,
                "lockfiles": lockfiles,
                "stats": {
                    lang: len(deps) for lang, deps in dependencies.items() if deps
                }
            }
        )
