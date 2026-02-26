"""Configuration loader for Security Bot."""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


def load_dotenv(env_path: Optional[str] = None) -> dict:
    """Load environment variables from .env file."""
    if env_path is None:
        env_path = Path(__file__).parent.parent.parent / ".env"
    else:
        env_path = Path(env_path)
    
    env_vars = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


@dataclass
class BotConfig:
    """Bot configuration loaded from environment variables."""
    
    # Discord Configuration
    token: str
    guild_id: int
    log_channel_id: int
    member_role_id: int
    unverified_role_id: int
    verify_channel_id: int
    
    # Security Settings
    new_account_threshold_days: int = 7
    
    @classmethod
    def load_from_env(cls, prefix: str = "BOT_", env_path: Optional[str] = None) -> "BotConfig":
        """Load configuration from environment variables."""
        # Load from .env file first
        env_vars = load_dotenv(env_path)
        
        def get_env(key: str, required: bool = True):
            full_key = f"{prefix}{key}"
            # Check environment first, then .env file
            value = os.environ.get(full_key) or env_vars.get(full_key)
            if required and not value:
                raise ValueError(f"Missing required environment variable: {full_key}")
            return value
        
        return cls(
            token=get_env("TOKEN"),
            guild_id=int(get_env("GUILD_ID")),
            log_channel_id=int(get_env("LOG_CHANNEL_ID")),
            member_role_id=int(get_env("MEMBER_ROLE_ID")),
            unverified_role_id=int(get_env("UNVERIFIED_ROLE_ID")),
            verify_channel_id=int(get_env("VERIFY_CHANNEL_ID")),
            new_account_threshold_days=int(get_env("NEW_ACCOUNT_THRESHOLD_DAYS", required=False) or 7)
        )


