#!/usr/bin/env python3
"""Efficient file reading with chunking support"""
from pathlib import Path
from typing import Iterator

from src.core.constants import Limits
from src.core.logger import get_logger

logger = get_logger("file_reader")


class ChunkReader:
    """Read files in chunks to prevent memory issues"""

    DEFAULT_CHUNK_SIZE = 8192  # 8KB chunks

    @classmethod
    def read_file_chunks(cls, file_path: Path, chunk_size: int = DEFAULT_CHUNK_SIZE) -> Iterator[str]:
        """
        Read file in chunks
        
        Args:
            file_path: Path to file
            chunk_size: Size of each chunk in bytes
            
        Yields:
            String chunks of the file
        """
        try:
            with open(file_path, errors='ignore') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")

    @classmethod
    def read_limited(cls, file_path: Path, max_bytes: int = Limits.MAX_FILE_CONTENT_SIZE) -> str:
        """
        Read limited amount of file content
        
        Args:
            file_path: Path to file
            max_bytes: Maximum bytes to read
            
        Returns:
            File content up to max_bytes
        """
        content = []
        bytes_read = 0

        for chunk in cls.read_file_chunks(file_path):
            if bytes_read + len(chunk) > max_bytes:
                # Add partial chunk to reach limit
                remaining = max_bytes - bytes_read
                content.append(chunk[:remaining])
                break
            content.append(chunk)
            bytes_read += len(chunk)

        return ''.join(content)

    @classmethod
    def count_lines_chunked(cls, file_path: Path) -> int:
        """
        Count lines in file without loading it all
        
        Args:
            file_path: Path to file
            
        Returns:
            Number of lines
        """
        line_count = 0
        for chunk in cls.read_file_chunks(file_path):
            line_count += chunk.count('\n')
        return line_count

    @classmethod
    def search_in_file(cls, file_path: Path, pattern: str, max_matches: int = 10) -> list:
        """
        Search for pattern in file without loading it all
        
        Args:
            file_path: Path to file
            pattern: Pattern to search
            max_matches: Maximum matches to return
            
        Returns:
            List of matches with line numbers
        """
        import re
        matches = []
        line_num = 1
        current_line = ""

        for chunk in cls.read_file_chunks(file_path):
            for char in chunk:
                current_line += char
                if char == '\n':
                    if pattern in current_line or re.search(pattern, current_line):
                        matches.append((line_num, current_line.strip()))
                        if len(matches) >= max_matches:
                            return matches
                    current_line = ""
                    line_num += 1

        # Check last line if no newline at end
        if current_line and (pattern in current_line or re.search(pattern, current_line)):
            matches.append((line_num, current_line.strip()))

        return matches
