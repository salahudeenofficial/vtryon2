"""
Configuration management for GPU server.
Loads and validates config.yaml at startup.
"""
import yaml
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

_config: Optional[Dict[str, Any]] = None


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config.yaml. If None, looks for configs/config.yaml
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file not found
        ValueError: If config is invalid
    """
    global _config
    
    if _config is not None:
        return _config
    
    if config_path is None:
        # Default to configs/config.yaml relative to this file
        base_dir = Path(__file__).parent.parent.parent
        config_path = base_dir / "configs" / "config.yaml"
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    logger.info(f"Loading configuration from {config_path}")
    
    with open(config_path, 'r') as f:
        _config = yaml.safe_load(f)
    
    # Validate required fields
    _validate_config(_config)
    
    logger.info(f"Configuration loaded successfully. Node ID: {get_node_id()}")
    
    return _config


def _validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration has all required fields."""
    required_fields = [
        ("server", "node_id"),
        ("security", "internal_auth_token"),
        ("asset_service", "callback_url"),
        ("asset_service", "internal_auth_token"),
        ("model", "model_type"),
        ("model", "model_version"),
    ]
    
    missing = []
    for section, field in required_fields:
        if section not in config:
            missing.append(f"{section}")
        elif field not in config[section]:
            missing.append(f"{section}.{field}")
    
    if missing:
        raise ValueError(f"Missing required config fields: {', '.join(missing)}")


def get_config() -> Dict[str, Any]:
    """Get loaded configuration. Loads if not already loaded."""
    if _config is None:
        return load_config()
    return _config


def get_node_id() -> str:
    """Get node ID from config."""
    return get_config()["server"]["node_id"]


def get_internal_auth_token() -> str:
    """Get internal auth token for CPU Bridge requests."""
    return get_config()["security"]["internal_auth_token"]


def get_asset_callback_url() -> str:
    """Get Asset Service callback URL."""
    return get_config()["asset_service"]["callback_url"]


def get_asset_auth_token() -> str:
    """Get auth token for Asset Service callbacks."""
    return get_config()["asset_service"]["internal_auth_token"]


def get_asset_timeout() -> int:
    """Get timeout for Asset Service callbacks (seconds)."""
    return get_config()["asset_service"]["timeout"]


def get_asset_retries() -> int:
    """Get number of retries for Asset Service callbacks."""
    return get_config()["asset_service"]["retries"]


def get_model_type() -> str:
    """Get model type."""
    return get_config()["model"]["model_type"]


def get_model_version() -> str:
    """Get model version."""
    return get_config()["model"]["model_version"]


def get_model_device() -> str:
    """Get model device (cuda/cpu)."""
    return get_config()["model"]["device"]


def get_log_level() -> str:
    """Get logging level."""
    return get_config().get("logging", {}).get("level", "INFO")

