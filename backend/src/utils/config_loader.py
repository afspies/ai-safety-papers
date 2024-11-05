import yaml
import os
from typing import Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_config() -> Dict:
    """
    Load and merge configuration from both default config and secrets.
    Default config (backend/config/config.yaml) is loaded first, then overlaid with
    secrets (secrets/config.yaml) if they exist.
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent.parent
    
    # Load default config
    default_config_path = project_root / 'backend' / 'config' / 'config.yaml'
    try:
        with open(default_config_path, 'r') as config_file:
            config = yaml.safe_load(config_file) or {}
    except Exception as e:
        logger.error(f"Error loading default config: {e}")
        config = {}

    # Set default paths relative to project root
    if 'data_dir' not in config:
        config['data_dir'] = str(project_root / 'data')
    if 'website' not in config:
        config['website'] = {}
    if 'content_path' not in config['website']:
        config['website']['content_path'] = str(project_root / 'ai-safety-site/content/en')

    # Load and merge secrets if they exist
    secrets_path = project_root / 'secrets' / 'config.yaml'
    if secrets_path.exists():
        try:
            with open(secrets_path, 'r') as secrets_file:
                secrets = yaml.safe_load(secrets_file)
                # Deep merge the configurations
                config = deep_merge(config, secrets)
        except Exception as e:
            logger.error(f"Error loading secrets: {e}")
    
    # Ensure data directory exists
    data_dir = Path(config['data_dir'])
    data_dir.mkdir(parents=True, exist_ok=True)
    
    return config

def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """
    Deep merge two dictionaries. dict2 values take precedence over dict1.
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result