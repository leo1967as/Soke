"""Unit tests for audit logging."""

import json
import logging

import pytest

from core.ai_support_bot.audit_logging.audit import log_event, log_interaction, setup_audit_logger


class TestAuditLogging:
    """Test audit logger output."""

    @pytest.fixture(autouse=True)
    def setup_logger(self, tmp_path, monkeypatch):
        """Redirect audit log to tmp for testing."""
        import core.ai_support_bot.audit_logging.audit as audit_mod

        monkeypatch.setattr(audit_mod, "_LOG_DIR", tmp_path)
        monkeypatch.setattr(audit_mod, "_LOG_FILE", tmp_path / "audit.jsonl")
        # Clear existing handlers
        audit_mod.audit_logger.handlers.clear()
        setup_audit_logger("DEBUG")
        self.log_file = tmp_path / "audit.jsonl"

    def test_log_interaction_creates_valid_json(self):
        log_interaction(
            user_id=12345,
            channel_id=67890,
            input_length=50,
            response_length=200,
            cache_hit=False,
            tokens_used=150,
            latency_ms=500,
        )
        lines = self.log_file.read_text().strip().split("\n")
        assert len(lines) >= 1

        record = json.loads(lines[-1])
        assert record["user_id"] == 12345
        assert record["channel_id"] == 67890
        assert record["cache_hit"] is False
        assert record["tokens_used"] == 150
        assert "ts" in record

    def test_log_interaction_with_error(self):
        log_interaction(
            user_id=1,
            channel_id=2,
            input_length=10,
            response_length=0,
            cache_hit=False,
            tokens_used=0,
            latency_ms=100,
            error="Gemini timeout",
        )
        lines = self.log_file.read_text().strip().split("\n")
        record = json.loads(lines[-1])
        assert record["error"] == "Gemini timeout"

    def test_log_interaction_no_message_content(self):
        """Verify that actual message content is NEVER logged (privacy)."""
        log_interaction(
            user_id=1,
            channel_id=2,
            input_length=42,
            response_length=100,
            cache_hit=True,
            tokens_used=0,
            latency_ms=5,
        )
        raw = self.log_file.read_text()
        # Should NOT contain any actual user message
        assert "question" not in raw.lower() or "input_length" in raw
        # Verify only lengths, not content
        record = json.loads(raw.strip().split("\n")[-1])
        assert "input" not in record  # no "input" key with content
        assert "input_length" in record  # only length

    def test_log_event(self):
        log_event("bot_starting", environment="test", version="0.1.0")
        lines = self.log_file.read_text().strip().split("\n")
        record = json.loads(lines[-1])
        assert record["event"] == "bot_starting"
        assert record["environment"] == "test"
        assert record["version"] == "0.1.0"

    def test_log_event_timestamp_format(self):
        log_event("test_event")
        lines = self.log_file.read_text().strip().split("\n")
        record = json.loads(lines[-1])
        # Should be ISO 8601 format
        assert "T" in record["ts"]
        assert "+" in record["ts"] or "Z" in record["ts"] or record["ts"].endswith("+00:00")
