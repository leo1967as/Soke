"""Structured JSON audit logger for all bot interactions.

Writes to logs/audit.jsonl — never logs actual message content in production.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

_LOG_DIR = Path("logs")
_LOG_FILE = _LOG_DIR / "audit.jsonl"

# Module-level logger
audit_logger = logging.getLogger("ai_support_bot.audit")


def setup_audit_logger(log_level: str = "INFO") -> None:
    """Configure the audit logger with file + console handlers."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    audit_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    audit_logger.propagate = False

    # Prevent duplicate handlers on reload
    if audit_logger.handlers:
        return

    # File handler — JSONL format
    fh = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(message)s"))
    audit_logger.addHandler(fh)

    # Console handler — human-readable
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    ch.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s | %(message)s"))
    audit_logger.addHandler(ch)


def log_interaction(
    user_id: int,
    channel_id: int,
    input_length: int,
    response_length: int,
    cache_hit: bool,
    tokens_used: int,
    latency_ms: int,
    error: str | None = None,
) -> None:
    """Log a single interaction as a JSON line.

    NOTE: We intentionally do NOT log message content for user privacy.
    """
    record = {
        "ts": datetime.now(UTC).isoformat(),
        "user_id": user_id,
        "channel_id": channel_id,
        "input_length": input_length,
        "response_length": response_length,
        "cache_hit": cache_hit,
        "tokens_used": tokens_used,
        "latency_ms": latency_ms,
    }
    if error:
        record["error"] = error

    audit_logger.info(json.dumps(record, ensure_ascii=False))


def log_event(event_type: str, **kwargs) -> None:
    """Log a generic system event (startup, shutdown, ingestion, etc.)."""
    record = {
        "ts": datetime.now(UTC).isoformat(),
        "event": event_type,
        **kwargs,
    }
    audit_logger.info(json.dumps(record, ensure_ascii=False))
