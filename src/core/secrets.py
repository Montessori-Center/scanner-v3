#!/usr/bin/env python3
"""Secret masking utilities for Scanner v3"""

def mask_secret(value: str) -> str:
    """Mask sensitive values in output
    
    Args:
        value: Secret value to mask
        
    Returns:
        Masked string like 'abc***xyz' or '***' for short values
    """
    if not value:
        return ""

    if len(value) <= 8:
        return "***"

    # Show first 3 and last 3 characters
    return f"{value[:3]}***{value[-3:]}"


def mask_in_dict(data: dict, sensitive_keys: list = None) -> dict:
    """Mask sensitive values in dictionary
    
    Args:
        data: Dictionary to process
        sensitive_keys: List of keys to mask (default: common secret keys)
        
    Returns:
        Dictionary with masked values
    """
    if sensitive_keys is None:
        sensitive_keys = [
            'password', 'token', 'key', 'secret', 'api_key',
            'private_key', 'auth', 'credential', 'pwd'
        ]

    result = {}
    for key, value in data.items():
        if any(sk in key.lower() for sk in sensitive_keys):
            result[key] = mask_secret(str(value)) if value else None
        elif isinstance(value, dict):
            result[key] = mask_in_dict(value, sensitive_keys)
        else:
            result[key] = value

    return result
