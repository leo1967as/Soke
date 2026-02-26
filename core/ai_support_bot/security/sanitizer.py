"""Input sanitization to defend against prompt injection and abuse."""

import re

MAX_MESSAGE_LENGTH = 500

INJECTION_PATTERNS: list[str] = [
    "ignore previous instructions",
    "ignore all instructions",
    "ignore your instructions",
    "disregard previous",
    "disregard all",
    "forget your rules",
    "forget all rules",
    "you are now",
    "act as if",
    "pretend you are",
    "new persona",
    "system:",
    "system prompt",
    "override:",
    "admin override",
    "jailbreak",
    "do anything now",
    "developer mode",
]

# Regex for common attack vectors
_CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```")
_BACKTICK_CHAIN_RE = re.compile(r"`{3,}")


def sanitize_user_input(text: str) -> str | None:
    """Sanitize user input for prompt injection.

    Returns:
        Cleaned text, or None if the message should be rejected.
    """
    if not text or not text.strip():
        return None

    text = text.strip()

    # Length cap
    if len(text) > MAX_MESSAGE_LENGTH:
        text = text[:MAX_MESSAGE_LENGTH]

    # Check injection patterns (case-insensitive)
    lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern in lower:
            return None

    # Strip code blocks (potential hidden instructions)
    text = _CODE_BLOCK_RE.sub("", text)
    text = _BACKTICK_CHAIN_RE.sub("", text)

    # Final whitespace cleanup
    text = text.strip()
    return text if text else None
