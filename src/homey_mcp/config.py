import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class HomeyMCPConfig(BaseSettings):
    # Homey configuratie
    homey_local_address: str = "YOUR_HOMEY_IP"  # User must set this
    homey_local_token: str = "your-token-here"  # User must set this

    # Server configuratie
    log_level: str = "INFO"
    cache_ttl: int = 300  # 5 minuten cache
    request_timeout: int = 30

    # Development settings
    offline_mode: bool = False  # Skip Homey connection voor testing
    demo_mode: bool = False  # Gebruik mock data

    model_config = {
        "env_file": [
            ".env",  # Current directory
            str(Path(__file__).parent.parent.parent / ".env"),  # Project root
        ],
        "case_sensitive": False,
    }


def get_config() -> HomeyMCPConfig:
    return HomeyMCPConfig()
