"""Agent configuration values."""

from __future__ import annotations

import os


AGENT_MODEL = (
    os.environ.get("API_MODEL")
    or os.environ.get("AGENT_MODEL")
    or "gemini-3-pro-preview"
)

API_KEY = os.environ.get("API_KEY") or os.environ.get("GOOGLE_API_KEY")
