#!/usr/bin/env python3
"""Input validation and security checks for Scanner v3"""
import os
import re
from pathlib import Path
from typing import List, Optional

from src.core.logger import get_logger

logger = get_logger("validators")


class InputValidator:
    """Validate and sanitize user inputs"""

    # Dangerous path patterns
    DANGEROUS_PATTERNS = [
        r'\.\.',  # Path traversal
        r'~/',     # Home directory access
        r'/etc/',  # System config
        r'/proc/', # Process info
        r'/sys/',  # System files
        r'/root/', # Root directory
        r'\\\\',   # UNC paths
    ]

    # Dangerous characters for command injection
    DANGEROUS_CHARS = ['|', ';', '&', '$', '`', '\n', '\r', '>', '<']

    # Maximum path length
    MAX_PATH_LENGTH = 4096

    # Maximum file size to process (100MB default)
    MAX_FILE_SIZE = 100 * 1024 * 1024

    @classmethod
    def validate_path(cls, path: Path, base_path: Optional[Path] = None) -> bool:
        """
        Validate path for security issues
        
        Args:
            path: Path to validate
            base_path: Optional base path to restrict access
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Convert to absolute path
            abs_path = path.resolve()
            path_str = str(abs_path)

            # Check path length
            if len(path_str) > cls.MAX_PATH_LENGTH:
                logger.warning(f"Path too long: {len(path_str)} chars")
                return False

            # Check for dangerous patterns
            for pattern in cls.DANGEROUS_PATTERNS:
                if re.search(pattern, path_str):
                    logger.warning(f"Dangerous pattern found in path: {pattern}")
                    return False

            # If base_path provided, ensure path is within it
            if base_path:
                base_abs = base_path.resolve()
                try:
                    abs_path.relative_to(base_abs)
                except ValueError:
                    logger.warning(f"Path {abs_path} is outside base path {base_abs}")
                    return False

            # Check if path exists and is accessible
            if abs_path.exists():
                # Check if we have read permission
                if not os.access(abs_path, os.R_OK):
                    logger.warning(f"No read permission for path: {abs_path}")
                    return False

                # If it's a file, check size
                if abs_path.is_file():
                    size = abs_path.stat().st_size
                    if size > cls.MAX_FILE_SIZE:
                        logger.warning(f"File too large: {size} bytes")
                        return False

            return True

        except Exception as e:
            logger.error(f"Error validating path {path}: {e}")
            return False

    @classmethod
    def sanitize_string(cls, input_str: str, max_length: int = 1000) -> str:
        """
        Sanitize string input to prevent injection attacks
        
        Args:
            input_str: String to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not input_str:
            return ""

        # Truncate if too long
        if len(input_str) > max_length:
            input_str = input_str[:max_length]

        # Remove dangerous characters
        for char in cls.DANGEROUS_CHARS:
            input_str = input_str.replace(char, '')

        # Remove non-printable characters
        input_str = ''.join(char for char in input_str if char.isprintable())

        return input_str.strip()

    @classmethod
    def validate_analyzers_list(cls, analyzers: str) -> Optional[List[str]]:
        """
        Validate comma-separated list of analyzers
        
        Args:
            analyzers: Comma-separated string of analyzer names
            
        Returns:
            List of valid analyzer names or None if invalid
        """
        if not analyzers:
            return None

        # Sanitize the input
        analyzers = cls.sanitize_string(analyzers)

        # Split and validate each analyzer name
        analyzer_list = []
        for name in analyzers.split(','):
            name = name.strip()
            # Only allow alphanumeric and underscore
            if re.match(r'^[a-zA-Z0-9_]+$', name):
                analyzer_list.append(name)
            else:
                logger.warning(f"Invalid analyzer name: {name}")

        return analyzer_list if analyzer_list else None


class RateLimiter:
    """Simple rate limiting for expensive operations"""

    def __init__(self, max_calls: int = 10, time_window: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    def check_limit(self) -> bool:
        """
        Check if operation is within rate limit
        
        Returns:
            True if within limit, False otherwise
        """
        import time
        current_time = time.time()

        # Remove old calls outside time window
        self.calls = [t for t in self.calls if current_time - t < self.time_window]

        # Check if within limit
        if len(self.calls) < self.max_calls:
            self.calls.append(current_time)
            return True

        return False
