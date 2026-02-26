"""Configuration loader with validation for all environment variables."""

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class BotConfig:
    """Immutable configuration for the AI Support Bot."""

    # Discord
    discord_token: str
    allowed_channel_ids: list[int]
    guild_id: int | None = None

    # OpenRouter / LLM Provider
    openrouter_api_key: str = ""
    llm_model: str = "openai/gpt-4o-mini"
    llm_provider: str = "openrouter"  # openrouter, openai, anthropic, etc.
    embedding_model: str = "openai/text-embedding-3-small"

    # Notion
    notion_token: str = ""
    notion_page_ids: list[str] = None  # Comma-separated page IDs in env
    notion_database_ids: list[str] = None  # Comma-separated database IDs in env

    # Google Sheets (base64-encoded service account JSON)
    google_sa_base64: str = ""
    sheets_spreadsheet_ids: list[str] = None  # Comma-separated in env

    # Cache
    cache_ttl_seconds: int = 3600

    # Rate Limiting
    rate_limit_max_calls: int = 5
    rate_limit_window_seconds: int = 60

    # Logging
    log_level: str = "INFO"
    environment: str = "development"

    # Ingestion
    ingestion_interval_seconds: int = 60


def _require(value: str | None, name: str) -> str:
    """Raise if a required env var is missing."""
    if not value:
        raise OSError(f"Missing required environment variable: {name}")
    return value


def _parse_channel_ids(raw: str | None) -> list[int]:
    """Parse comma-separated channel IDs."""
    if not raw:
        return []
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def _parse_ids(raw: str | None) -> list[str]:
    """Parse comma-separated string IDs."""
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def load_config(env_path: str | Path | None = None) -> BotConfig:
    """Load and validate configuration from environment / .env file."""
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()

    return BotConfig(
        discord_token=_require(os.getenv("DISCORD_BOT_TOKEN"), "DISCORD_BOT_TOKEN"),
        allowed_channel_ids=_parse_channel_ids(os.getenv("ALLOWED_CHANNEL_IDS")),
        guild_id=int(gid) if (gid := os.getenv("BOT_GUILD_ID")) else None,
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", "openai/gpt-4o-mini"),
        llm_provider=os.getenv("LLM_PROVIDER", "openrouter"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small"),
        notion_token=os.getenv("NOTION_TOKEN", ""),
        notion_page_ids=_parse_ids(os.getenv("NOTION_PAGE_IDS")),
        notion_database_ids=_parse_ids(os.getenv("NOTION_DATABASE_IDS")),
        google_sa_base64=os.getenv("GOOGLE_SA_BASE64", ""),
        sheets_spreadsheet_ids=_parse_ids(os.getenv("SHEETS_SPREADSHEET_IDS")),
        cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "3600")),
        rate_limit_max_calls=int(os.getenv("RATE_LIMIT_MAX_CALLS", "5")),
        rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        environment=os.getenv("ENVIRONMENT", "development"),
        ingestion_interval_seconds=int(os.getenv("INGESTION_INTERVAL_SECONDS", "3600")),
    )


def load_google_credentials(config: BotConfig):
    """Decode base64 service account JSON and return Credentials object."""
    from google.oauth2.service_account import Credentials

    if not config.google_sa_base64:
        raise OSError("GOOGLE_SA_BASE64 is not set")

    info = json.loads(base64.b64decode(config.google_sa_base64))
    return Credentials.from_service_account_info(
        info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ],
    )
