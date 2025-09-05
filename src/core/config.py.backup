"""Configuration module for Scanner v3"""
from pydantic_settings import BaseSettings
from typing import List, Dict, Any, Optional
from pathlib import Path


class Settings(BaseSettings):
    """Main configuration for Scanner system"""
    
    # Performance profile
    profile: str = "balanced"
    log_level: str = "info"
    output_dir: str = "output"
    log_dir: str = "logs"
    max_file_size: int = 500000
    scan_timeout: int = 120
    debug: bool = False
    
    # Default exclusions - CRITICAL for performance
    DEFAULT_EXCLUDE: List[str] = [
        "**/.git/**",
        "**/node_modules/**", 
        "**/vendor/**",
        "**/.venv/**",
        "**/venv/**",
        "**/dist/**",
        "**/build/**",
        "**/coverage/**",
        "**/.pytest_cache/**",
        "**/__pycache__/**",
        "**/target/**",
        "**/*.lock",
        "**/*.log",
        "**/*.sqlite",
        "**/*.db",
        "**/output/**",
    ]
    
    # Performance profiles
    PROFILES: Dict[str, Dict[str, Any]] = {
        "fast": {
            "max_file_size": 100_000,  # 100KB
            "scan_timeout": 30,
            "max_analyzers": 5,
        },
        "balanced": {
            "max_file_size": 500_000,  # 500KB
            "scan_timeout": 120,
            "max_analyzers": 10,
        },
        "deep": {
            "max_file_size": 2_000_000,  # 2MB
            "scan_timeout": 300,
            "max_analyzers": 20,
        }
    }
    
    def get_profile_settings(self) -> Dict[str, Any]:
        """Get current profile settings"""
        return self.PROFILES.get(self.profile, self.PROFILES["balanced"])
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "SCANNER_"  # All env vars must start with SCANNER_
