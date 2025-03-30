import yaml
import os
import re
from typing import Dict, Any
from pathlib import Path
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def load_config() -> Dict:
    """
    Load and merge configuration from default config, secrets, and environment variables.
    Order of precedence: environment variables > secrets > default config
    """
    # Load environment variables from .env files
    project_root = Path(__file__).parent.parent.parent.parent
    
    # Load from home directory first
    home_env_path = Path.home() / ".env"
    if home_env_path.exists():
        logger.info(f"Loading environment variables from {home_env_path}")
        load_dotenv(home_env_path)
    
    # Then try to load from both project root and backend directory
    load_dotenv(project_root / ".env")
    load_dotenv(project_root / "backend" / ".env")
    
    # Load default config
    default_config_path = project_root / 'backend' / 'config' / 'config.yaml'
    try:
        with open(default_config_path, 'r') as config_file:
            config_content = config_file.read()
            # Replace environment variables in config
            config_content = replace_env_vars(config_content)
            config = yaml.safe_load(config_content) or {}
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
                secrets_content = secrets_file.read()
                # Replace environment variables in secrets
                secrets_content = replace_env_vars(secrets_content)
                secrets = yaml.safe_load(secrets_content)
                # Deep merge the configurations
                config = deep_merge(config, secrets)
        except Exception as e:
            logger.error(f"Error loading secrets: {e}")
    
    # Check if we're in development mode
    if os.environ.get('DEVELOPMENT_MODE') == 'true':
        logger.info("Running in development mode - using mock/placeholder API keys")
        # Override API keys with development placeholders if needed
        if not config.get('semantic_scholar', {}).get('api_key') or config['semantic_scholar']['api_key'] == "${SEMANTIC_SCHOLAR_API_KEY}":
            logger.info("Using mock Semantic Scholar API key for development")
            if 'semantic_scholar' not in config:
                config['semantic_scholar'] = {}
            config['semantic_scholar']['api_key'] = "development_placeholder_key"
            
        if not config.get('anthropic', {}).get('api_key') or config['anthropic']['api_key'] == "${ANTHROPIC_API_KEY}":
            logger.info("Using mock Anthropic API key for development")
            if 'anthropic' not in config:
                config['anthropic'] = {}
            config['anthropic']['api_key'] = "development_placeholder_key"
            
        if not config.get('supabase', {}).get('url') or config['supabase']['url'] == "${SUPABASE_URL}":
            logger.info("Using mock Supabase URL for development")
            if 'supabase' not in config:
                config['supabase'] = {}
            config['supabase']['url'] = "https://example.supabase.co"
            
        if not config.get('supabase', {}).get('key') or config['supabase']['key'] == "${SUPABASE_KEY}":
            logger.info("Using mock Supabase key for development")
            if 'supabase' not in config:
                config['supabase'] = {}
            config['supabase']['key'] = "fake_key_for_testing"
    
    # Ensure data directory exists
    data_dir = Path(config['data_dir'])
    data_dir.mkdir(parents=True, exist_ok=True)
    
    return config

def replace_env_vars(content: str) -> str:
    """Replace ${ENV_VAR} in content with environment variables."""
    pattern = r'\${([A-Za-z0-9_]+)}'
    
    def replace(match):
        env_var = match.group(1)
        return os.environ.get(env_var, match.group(0))
    
    return re.sub(pattern, replace, content)

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