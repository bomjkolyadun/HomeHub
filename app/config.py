"""
Configuration management for Homehub (Flask-native)
"""
import copy
from flask import current_app
from app.default_config import DEFAULT_VOD_CONFIG

def deep_merge(base, override):
    """
    Recursively merge two dictionaries, with override values taking precedence.
    Returns a new dictionary without modifying either input.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def get_default_config():
    """Return a copy of the default configuration dictionary."""
    return copy.deepcopy(DEFAULT_VOD_CONFIG)

def get_config():
    """
    Get the merged configuration from Flask's config object.
    Uses instance/environment overrides with defaults from app package.
    """
    config = get_default_config()
    if 'VOD_CONFIG' in current_app.config:
        config = deep_merge(config, current_app.config['VOD_CONFIG'])
    return config