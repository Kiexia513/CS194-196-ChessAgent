# limingrui

# API configuration for LLM agents

import os
from pathlib import Path
from typing import Optional


def load_api_keys() -> dict:
    """
    Load API keys from api.txt file
    
    Returns:
        Dictionary with API keys
    """
    api_keys = {
        "deepseek": None,
        "google": None,
        "openai": None
    }
    
    # Try to load from src/api/api.txt
    api_file = Path(__file__).parent.parent / "api" / "api.txt"
    
    if api_file.exists():
        try:
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Parse DeepSeek key
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('deepseek:'):
                        api_keys["deepseek"] = line.split(':', 1)[1].strip()
                    elif line.startswith('google:'):
                        api_keys["google"] = line.split(':', 1)[1].strip()
                    elif line.startswith('chatgpt5:') or line.startswith('openai:'):
                        api_keys["openai"] = line.split(':', 1)[1].strip()
        except Exception as e:
            print(f"  Failed to load API keys from {api_file}: {e}")
    
    # Try environment variables as fallback
    api_keys["deepseek"] = api_keys["deepseek"] or os.getenv("DEEPSEEK_API_KEY")
    api_keys["google"] = api_keys["google"] or os.getenv("GOOGLE_API_KEY")
    api_keys["openai"] = api_keys["openai"] or os.getenv("OPENAI_API_KEY")
    
    return api_keys


# Load API keys at module import
API_KEYS = load_api_keys()

# API endpoints
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Default models
DEFAULT_MODELS = {
    "deepseek": "deepseek-reasoner",  # Use deepseek-reasoner for deeper thinking
    "openai": "gpt-4o-mini",  # Use gpt-4o-mini or gpt-4o (gpt-5 doesn't exist yet)
    "google": "gemini-pro"
}

# LLM parameters
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 4096  # Increased to allow longer reasoning output (deepseek-reasoner needs more)
DEFAULT_TIMEOUT = 180  # seconds (3 minutes for reasoning models to think)


def get_api_key(service: str) -> Optional[str]:
    return API_KEYS.get(service)


def print_api_status(): 
    print("\n API Key Status:")
    for service, key in API_KEYS.items():
        status = " Available" if key else " Not set"
        masked_key = f"{key[:10]}...{key[-4:]}" if key else "None"
        print(f"   {service:10}: {status:15} ({masked_key})")


__all__ = [
    'API_KEYS',
    'get_api_key',
    'print_api_status',
    'DEEPSEEK_API_URL',
    'OPENAI_API_URL',
    'GOOGLE_API_URL',
    'DEFAULT_MODELS',
    'DEFAULT_TEMPERATURE',
    'DEFAULT_MAX_TOKENS',
    'DEFAULT_TIMEOUT'
]

