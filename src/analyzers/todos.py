"""TODOs and technical debt analyzer"""
import re
from typing import Dict, List
from collections import defaultdict

from src.core.base import BaseAnalyzer
from src.core.models import ScanResult, AnalysisResult


class TodosAnalyzer(BaseAnalyzer):
    """Find and analyze TODOs, FIXMEs, HACKs and other technical debt markers"""
    
    name = "todos"
    description = "Extract TODO, FIXME, HACK, BUG comments and technical debt"
    
    # Patterns for different markers
    PATTERNS = {
        'TODO': r'#\s*TODO:?\s*(.*)|//\s*TODO:?\s*(.*)|/\*\s*TODO:?\s*(.*?)\*/',
        'FIXME': r'#\s*FIXME:?\s*(.*)|//\s*FIXME:?\s*(.*)|/\*\s*FIXME:?\s*(.*?)\*/',
        'HACK': r'#\s*HACK:?\s*(.*)|//\s*HACK:?\s*(.*)|/\*\s*HACK:?\s*(.*?)\*/',
        'BUG': r'#\s*BUG:?\s*(.*)|//\s*BUG:?\s*(.*)|/\*\s*BUG:?\s*(.*?)\*/',
        'XXX': r'#\s*XXX:?\s*(.*)|//\s*XXX:?\s*(.*)|/\*\s*XXX:?\s*(.*?)\*/',
        'OPTIMIZE': r'#\s*OPTIMIZE:?\s*(.*)|//\s*OPTIMIZE:?\s*(.*)|/\*\s*OPTIMIZE:?\s*(.*?)\*/',
        'REFACTOR': r'#\s*REFACTOR:?\s*(.*)|//\s*REFACTOR:?\s*(.*)|/\*\s*REFACTOR:?\s*(.*?)\*/',
        'NOTE': r'#\s*NOTE:?\s*(.*)|//\s*NOTE:?\s*(.*)|/\*\s*NOTE:?\s*(.*?)\*/',
        'WARNING': r'#\s*WARNING:?\s*(.*)|//\s*WARNING:?\s*(.*)|/\*\s*WARNING:?\s*(.*?)\*/',
    }
    
    async def analyze(self, scan: ScanResult) -> AnalysisResult:
        """Analyze technical debt markers"""
        
        todos = defaultdict(list)
        files_with_debt = set()
        
        # Only check source code files
        code_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.php', '.java', 
            '.go', '.rs', '.rb', '.cs', '.cpp', '.c', '.h', '.hpp',
            '.swift', '.kt', '.scala', '.lua', '.r', '.m', '.dart'
        }
        
        for file in scan.files:
            if file.suffix not in code_extensions:
                continue
            
            try:
                content = file.read_text(errors='ignore')[:100000]  # First 100KB
                file_has_debt = False
                
                # Split into lines for line numbers
                lines = content.split('\n')
                
                for tag, pattern in self.PATTERNS.items():
                    # Find all matches in the file
                    for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                        # Get the actual comment text
                        groups = match.groups()
                        comment_text = next((g for g in groups if g), '').strip()
                        
                        # Find line number
                        line_num = content[:match.start()].count('\n') + 1
                        
                        if comment_text:
                            todos[tag].append({
                                'file': str(file.path.relative_to(scan.root)),
                                'line': line_num,
                                'text': comment_text[:200]  # Max 200 chars
                            })
                            file_has_debt = True
                            
                            # Limit per tag
                            if len(todos[tag]) >= 50:
                                break
                
                if file_has_debt:
                    files_with_debt.add(str(file.path.relative_to(scan.root)))
                    
            except:
                pass
        
        # Calculate statistics
        total_count = sum(len(items) for items in todos.values())
        
        # Priority classification
        high_priority = len(todos['FIXME']) + len(todos['BUG'])
        medium_priority = len(todos['TODO']) + len(todos['HACK']) + len(todos['XXX'])
        low_priority = len(todos['OPTIMIZE']) + len(todos['REFACTOR']) + len(todos['NOTE'])
        
        # Convert defaultdict to dict and limit items
        todos_dict = {}
        for tag in self.PATTERNS.keys():
            if todos[tag]:
                todos_dict[tag] = todos[tag][:20]  # Max 20 per type
        
        return AnalysisResult(
            analyzer=self.name,
            data={
                "todos": todos_dict,
                "total": total_count,
                "files_with_debt": len(files_with_debt),
                "by_type": {
                    tag: len(todos[tag]) for tag in self.PATTERNS.keys()
                },
                "by_priority": {
                    "high": high_priority,
                    "medium": medium_priority, 
                    "low": low_priority
                },
                "top_files": list(files_with_debt)[:10]
            }
        )
