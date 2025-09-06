#!/usr/bin/env python3
"""Constants and limits for Scanner v3"""

class Limits:
    """Limits for analyzers to prevent memory issues"""

    # File processing limits
    MAX_FILE_CONTENT_SIZE = 100_000  # 100KB for content analysis
    MAX_FILES_TO_ANALYZE = 100  # Max files per analyzer

    # Per-analyzer item limits
    MAX_FUNCTIONS_PER_FILE = 20
    MAX_ENDPOINTS = 100
    MAX_TODOS_PER_TYPE = 50
    MAX_DEPENDENCIES = 100
    MAX_ENV_VARS = 100
    MAX_TABLES = 50
    MAX_MIGRATIONS = 30
    MAX_MODELS = 30
    MAX_VULNERABILITIES = 20
    MAX_COMMITS = 20

    # Display limits (for output)
    MAX_ITEMS_TO_DISPLAY = 10
    MAX_DIRECTORIES_TO_SHOW = 20
    MAX_ENTRY_POINTS = 10

    # Text limits
    MAX_TEXT_PREVIEW = 200  # Characters for text preview
    MAX_LINE_LENGTH = 100  # For TODO/error text
