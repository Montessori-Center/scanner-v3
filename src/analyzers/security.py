"""Security vulnerabilities analyzer"""
import re
from typing import List, Dict
from pathlib import Path

from src.core.base import BaseAnalyzer
from src.core.models import ScanResult, AnalysisResult

from src.core.logger import get_logger


class SecurityAnalyzer(BaseAnalyzer):
    """Analyze potential security vulnerabilities"""
    
    name = "security"

    logger = get_logger("security")
    description = "Find potential security issues and vulnerable patterns"

    
    # Security patterns to check
    PATTERNS = {
        'hardcoded_secrets': [
            r'(?i)(api[_-]?key|apikey|secret|password|passwd|pwd|token|auth)["\']?\s*[:=]\s*["\'][^"\']+["\']',
            r'(?i)(aws_access_key_id|aws_secret_access_key)\s*=\s*["\'][^"\']+["\']',
        ],
        'sql_injection': [
            r'(?i)(select|insert|update|delete|drop)\s+.*\+\s*[^"\'\s]+',  # String concatenation in SQL
            r'(?i)query\(["\'].*%[sd].*["\'].*%',  # String formatting in query
            r'(?i)f["\'].*select.*from.*\{',  # f-string in SQL
        ],
        'xss_vulnerabilities': [
            r'innerHTML\s*=\s*[^"\'\s]+',  # Direct innerHTML assignment
            r'document\.write\([^)]*\+',  # document.write with concatenation
            r'v-html\s*=\s*["\'][^"\']*\{',  # Vue v-html with interpolation
        ],
        'command_injection': [
            r'(?i)exec\([^)]*\+',  # exec with concatenation
            r'(?i)system\([^)]*\$',  # system with variables
            r'(?i)eval\([^)]*\$',  # eval with variables
            r'subprocess\.(call|run|Popen)\([^)]*\+',  # subprocess with concatenation
        ],
        'weak_crypto': [
            r'(?i)md5\s*\(',  # MD5 usage
            r'(?i)sha1\s*\(',  # SHA1 usage
            r'(?i)des\s*\(',  # DES encryption
            r'(?i)random\s*\(',  # Weak random for security
        ],
        'insecure_deserialization': [
            r'pickle\.loads?\(',  # Python pickle
            r'yaml\.load\([^)]*\)',  # YAML load without safe loader
            r'eval\(.*request\.',  # eval with request data
            r'unserialize\(',  # PHP unserialize
        ]
    }
    
    # File patterns that often contain sensitive data
    SENSITIVE_FILES = [
        '.env', '.env.local', '.env.production',
        'config.json', 'settings.py', 'config.php',
        '.git/config', '.npmrc', '.pypirc',
        'id_rsa', 'id_dsa', '.pem', '.key', '.cert'
    ]
    
    async def analyze(self, scan: ScanResult) -> AnalysisResult:
        """Analyze security vulnerabilities"""
        
        vulnerabilities = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        sensitive_files = []
        vulnerable_dependencies = []
        security_headers = []
        
        for file in scan.files:
            # Check for sensitive files
            if any(file.name.endswith(pattern) for pattern in self.SENSITIVE_FILES):
                sensitive_files.append(str(file.path.relative_to(scan.root)))
                
            # Only scan code files
            if file.suffix not in ['.py', '.js', '.jsx', '.ts', '.tsx', '.php', '.rb', '.java', '.go']:
                continue
            
            try:
                content = file.read_text(errors='ignore')[:100000]  # First 100KB
                
                # Check security patterns
                for vuln_type, patterns in self.PATTERNS.items():
                    for pattern in patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            for match in matches[:3]:  # Max 3 per pattern per file
                                # Classify severity
                                severity = self._classify_severity(vuln_type)
                                
                                vuln_info = {
                                    'type': vuln_type,
                                    'file': str(file.path.relative_to(scan.root)),
                                    'pattern': pattern[:50],
                                    'match': str(match)[:100] if not self._is_secret(vuln_type) else '***REDACTED***'
                                }
                                
                                vulnerabilities[severity].append(vuln_info)
                                
                                # Limit total vulnerabilities
                                if len(vulnerabilities[severity]) >= 20:
                                    break
                
                # Check for security headers (for web files)
                if file.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                    if 'X-Frame-Options' in content:
                        security_headers.append('X-Frame-Options')
                    if 'Content-Security-Policy' in content:
                        security_headers.append('CSP')
                    if 'Strict-Transport-Security' in content:
                        security_headers.append('HSTS')
                        
            except Exception as e:
                self.logger.debug(f"Error in security header detection: {e}")
        
        # Check package files for known vulnerable packages
        vulnerable_packages = self._check_vulnerable_packages(scan)
        
        # Calculate totals
        total_vulnerabilities = sum(
            len(vulnerabilities[sev]) for sev in vulnerabilities
        )
        
        return AnalysisResult(
            analyzer=self.name,
            data={
                "vulnerabilities": vulnerabilities,
                "total": total_vulnerabilities,
                "by_severity": {
                    sev: len(items) for sev, items in vulnerabilities.items()
                },
                "sensitive_files": sensitive_files[:10],
                "vulnerable_packages": vulnerable_packages[:10],
                "security_headers": security_headers,
                "has_critical": len(vulnerabilities['critical']) > 0,
                "recommendations": self._get_recommendations(vulnerabilities)
            }
        )
    
    def _classify_severity(self, vuln_type: str) -> str:
        """Classify vulnerability severity"""
        critical = ['hardcoded_secrets', 'sql_injection', 'command_injection']
        high = ['xss_vulnerabilities', 'insecure_deserialization']
        medium = ['weak_crypto']
        
        if vuln_type in critical:
            return 'critical'
        elif vuln_type in high:
            return 'high'
        elif vuln_type in medium:
            return 'medium'
        else:
            return 'low'
    
    def _is_secret(self, vuln_type: str) -> bool:
        """Check if vulnerability type contains secrets"""
        return vuln_type in ['hardcoded_secrets']
    
    def _check_vulnerable_packages(self, scan: ScanResult) -> List[str]:
        """Check for known vulnerable packages"""
        vulnerable = []
        
        # Common vulnerable packages (simplified check)
        known_vulnerable = {
            'python': ['pycrypto', 'rsa<4.0', 'django<2.2', 'flask<1.0'],
            'javascript': ['lodash<4.17.19', 'axios<0.21.1', 'jquery<3.5.0']
        }
        
        for file in scan.files:
            if file.name == 'requirements.txt':
                try:
                    content = file.read_text()
                    for pkg in known_vulnerable['python']:
                        if pkg.split('<')[0] in content.lower():
                            vulnerable.append(f"python:{pkg}")
                except Exception as e:
                    self.logger.debug(f"Error checking Python packages: {e}")
                    
            elif file.name == 'package.json':
                try:
                    content = file.read_text()
                    for pkg in known_vulnerable['javascript']:
                        if pkg.split('<')[0] in content.lower():
                            vulnerable.append(f"javascript:{pkg}")
                except Exception as e:
                    self.logger.debug(f"Error checking JavaScript packages: {e}")
        
        return vulnerable
    
    def _get_recommendations(self, vulnerabilities: Dict) -> List[str]:
        """Get security recommendations based on findings"""
        recommendations = []
        
        if vulnerabilities['critical']:
            recommendations.append("URGENT: Remove hardcoded secrets and use environment variables")
            recommendations.append("Fix SQL injection vulnerabilities by using parameterized queries")
            
        if vulnerabilities['high']:
            recommendations.append("Implement input validation and output encoding to prevent XSS")
            recommendations.append("Use safe deserialization methods")
            
        if vulnerabilities['medium']:
            recommendations.append("Replace weak cryptographic algorithms with modern alternatives")
            
        if not recommendations:
            recommendations.append("No critical security issues found")
            
        return recommendations[:5]
