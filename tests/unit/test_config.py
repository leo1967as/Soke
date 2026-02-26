"""Unit tests for configuration loading and validation."""

import os
from unittest.mock import patch

import pytest

from core.ai_support_bot.config import BotConfig, _parse_channel_ids, _require, load_config


class TestRequire:
    """Test the _require helper."""

    def test_returns_value_if_present(self):
        assert _require("hello", "MY_VAR") == "hello"

    def test_raises_on_none(self):
        with pytest.raises(EnvironmentError, match="MY_VAR"):
            _require(None, "MY_VAR")

    def test_raises_on_empty_string(self):
        with pytest.raises(EnvironmentError, match="MY_VAR"):
            _require("", "MY_VAR")


class TestParseChannelIds:
    """Test channel ID parsing."""

    def test_single_id(self):
        assert _parse_channel_ids("12345") == [12345]

    def test_multiple_ids(self):
        assert _parse_channel_ids("111,222,333") == [111, 222, 333]

    def test_whitespace_handling(self):
        assert _parse_channel_ids(" 111 , 222 , 333 ") == [111, 222, 333]

    def test_none_returns_empty(self):
        assert _parse_channel_ids(None) == []

    def test_empty_string_returns_empty(self):
        assert _parse_channel_ids("") == []

    def test_trailing_comma_ignored(self):
        assert _parse_channel_ids("111,222,") == [111, 222]


class TestBotConfig:
    """Test BotConfig dataclass."""

    def test_frozen_immutable(self):
        config = BotConfig(discord_token="test", allowed_channel_ids=[])
        with pytest.raises(AttributeError):
            config.discord_token = "changed"

    def test_defaults(self):
        config = BotConfig(discord_token="test", allowed_channel_ids=[])
        assert config.llm_model == "openai/gpt-4o-mini"
        assert config.llm_provider == "openrouter"
        assert config.cache_ttl_seconds == 3600
        assert config.rate_limit_max_calls == 5
        assert config.log_level == "INFO"
        assert config.environment == "development"


class TestLoadConfig:
    """Test load_config with mocked environment."""

    @patch.dict(os.environ, {
        "DISCORD_BOT_TOKEN": "test_token_123",
        "ALLOWED_CHANNEL_IDS": "111,222",
        "OPENROUTER_API_KEY": "openrouter_key",
        "LLM_MODEL": "openai/gpt-4o",
        "LLM_PROVIDER": "openrouter",
        "NOTION_TOKEN": "notion_secret",
        "LOG_LEVEL": "DEBUG",
        "ENVIRONMENT": "production",
    }, clear=False)
    def test_loads_from_env(self):
        config = load_config()
        assert config.discord_token == "test_token_123"
        assert config.allowed_channel_ids == [111, 222]
        assert config.openrouter_api_key == "openrouter_key"
        assert config.llm_model == "openai/gpt-4o"
        assert config.llm_provider == "openrouter"
        assert config.notion_token == "notion_secret"
        assert config.log_level == "DEBUG"
        assert config.environment == "production"

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_token_raises(self):
        with pytest.raises(EnvironmentError, match="DISCORD_BOT_TOKEN"):
            load_config()
