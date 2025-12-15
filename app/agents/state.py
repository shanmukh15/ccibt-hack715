from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from app.agents.entitlements import PLAN_ENTITLEMENTS

_SESSION_STATE: Dict[str, Dict[str, Any]] = {}


def init_session_state(
    session_id: str, *, user_profile: Dict[str, Any] | None = None
) -> None:
    """Initialize the session state."""
    if session_id not in _SESSION_STATE:
        _SESSION_STATE[session_id] = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "pricing": {"BRONZE": 100, "SILVER": 200, "GOLD": 300},
            "entitlements": PLAN_ENTITLEMENTS,
        }
    if user_profile is not None:
        _SESSION_STATE[session_id]["user_profile"] = user_profile


def get_session_state(session_id: str) -> Dict[str, Any]:
    return _SESSION_STATE.get(session_id, {})


def update_session_state(session_id: str, **kwargs: Any) -> None:
    state = _SESSION_STATE.setdefault(session_id, {})
    state.update(kwargs)
    state["last_updated_at"] = datetime.now(timezone.utc).isoformat()
