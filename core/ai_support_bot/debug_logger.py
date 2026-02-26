"""Clean file-based debug logger for the RAG pipeline.

Writes a clean, readable log file for every user query,
showing exactly what was sent to and received from each AI call.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("ai_support_bot.debug")

LOG_DIR = Path(__file__).parent / "debug_logs"
LOG_DIR.mkdir(exist_ok=True)


class PipelineDebugLogger:
    """Logs every step of the RAG pipeline to a clean, readable file."""

    def __init__(self):
        self._steps: list[dict] = []
        self._question: str = ""
        self._timestamp: str = ""

    def start(self, question: str):
        """Start a new pipeline trace."""
        self._steps = []
        self._question = question
        self._timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def log_step(self, step_name: str, **kwargs):
        """Log a single step with key-value data."""
        entry = {"step": step_name, **kwargs}
        self._steps.append(entry)

    def save(self):
        """Write the full pipeline trace to a clean text file."""
        safe_q = self._question[:30].replace(" ", "_").replace("/", "")
        filename = f"{self._timestamp}_{safe_q}.txt"
        filepath = LOG_DIR / filename

        lines = []
        lines.append("=" * 70)
        lines.append(f"  PIPELINE DEBUG LOG")
        lines.append(f"  Time: {self._timestamp}")
        lines.append(f"  Question: {self._question}")
        lines.append("=" * 70)
        lines.append("")

        for entry in self._steps:
            step = entry.get("step", "unknown")
            lines.append(f"{'─' * 50}")
            lines.append(f"📌 {step}")
            lines.append(f"{'─' * 50}")
            for k, v in entry.items():
                if isinstance(v, list):
                    lines.append(f"  {k}: ({len(v)} items)")
                    for i, item in enumerate(v):
                        # Truncate each item for readability
                        preview = str(item)[:200].replace("\n", " ↵ ")
                        lines.append(f"    [{i}] {preview}")
                elif isinstance(v, str) and len(v) > 200:
                    lines.append(f"  {k}:")
                    # Print full content for important fields
                    for line in v.split("\n"):
                        lines.append(f"    {line}")
                else:
                    lines.append(f"  {k}: {v}")
            lines.append("")

        lines.append("=" * 70)
        lines.append("END OF LOG")
        lines.append("=" * 70)

        filepath.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Pipeline debug log saved: {filepath}")
        return str(filepath)


# Singleton instance
pipeline_logger = PipelineDebugLogger()
