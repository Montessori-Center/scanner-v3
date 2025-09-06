#!/usr/bin/env python3
"""Webhooks and External Integrations Analyzer"""
import re

from src.core.base import BaseAnalyzer
from src.core.logger import get_logger
from src.core.models import AnalysisResult, ScanResult


class WebhooksAnalyzer(BaseAnalyzer):
    """Find webhooks, external APIs, and integration points"""

    name = "webhooks"
    description = "Find webhooks and external integrations"

    logger = get_logger("webhooks")

    WEBHOOK_PATTERNS = [
        r'webhook[_\s]?url.*?["\']([^"\']+)',
        r'https?://hooks\.[^"\']+',
        r'slack\.com/api/[^"\']+',
        r'discord\.com/api/webhooks/[^"\']+',
    ]

    async def analyze(self, scan_result: ScanResult) -> AnalysisResult:
        """Analyze webhooks and integrations"""
        webhooks = []

        for file_info in scan_result.files[:100]:  # Limit files
            if file_info.extension in ['.py', '.js', '.ts', '.json', '.yml', '.yaml', '.env']:
                try:
                    content = file_info.path.read_text(errors='ignore')
                    for pattern in self.WEBHOOK_PATTERNS:
                        for match in re.finditer(pattern, content, re.IGNORECASE):
                            url = match.group(1) if match.lastindex else match.group(0)
                            webhooks.append({
                                'url': url[:50] + '***' if len(url) > 50 else url,
                                'file': str(file_info.path.name),
                                'type': self._detect_webhook_type(url)
                            })
                            if len(webhooks) >= 20:
                                break
                except Exception:
                    continue

        return AnalysisResult(
            analyzer=self.name,
            data={
                "webhooks": webhooks,
                "total": len(webhooks),
                "types": list(set(w['type'] for w in webhooks))
            }
        )

    def _detect_webhook_type(self, url: str) -> str:
        """Detect webhook service type"""
        url_lower = url.lower()
        if 'slack' in url_lower:
            return 'slack'
        elif 'discord' in url_lower:
            return 'discord'
        elif 'telegram' in url_lower:
            return 'telegram'
        elif 'github' in url_lower:
            return 'github'
        else:
            return 'custom'
