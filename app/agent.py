# ruff: noqa
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps.app import App

from .agents.config import AGENT_MODEL, API_KEY
from .agents.entitlement_tools import check_entitlement
from .agents.prompts import (
    ACTION_INSTRUCTION,
    GLOBAL_INSTRUCTION,
    ORCHESTRATOR_INSTRUCTION,
    RECOMMENDATION_INSTRUCTION,
    SERVICE_INSTRUCTION,
)
from .agents.state import update_session_state
from .agents.user_registry import set_user_plan


def _configure_platform() -> None:
    """Configure authentication depending on environment variables."""

    api_key = API_KEY
    if api_key:
        # Allow overriding runtime API key without forcing Vertex AI defaults.
        os.environ.setdefault("GOOGLE_API_KEY", api_key)
        os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
        os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", False)
        return

    # Vertex AI (ADC) fallback for Google Cloud deployments.
    try:
        import google.auth

        _, project_id = google.auth.default()
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise RuntimeError(
            "Failed to obtain Google Cloud credentials. Set the API_KEY "
            "environment variable for direct Gemini API access or configure "
            "Application Default Credentials."
        ) from exc

    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


_configure_platform()


def update_user_dataplan(*, uid: str, plan: str, session_id: str | None = None) -> str:
    """Tool: Update a user's data plan to GOLD/SILVER/BRONZE.

    Optionally updates the session state with the new current plan.
    Returns a human-readable status string.
    """
    success = set_user_plan(uid, plan)
    if not success:
        return "Unable to update plan. Verify UID and plan (GOLD/SILVER/BRONZE)."

    if session_id:
        update_session_state(session_id, current_plan=plan.upper())
    return f"Plan updated to {plan.upper()} for user {uid}."

action_agent = Agent(
    model=AGENT_MODEL,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=ACTION_INSTRUCTION,
    name="action_agent",
    tools=[update_user_dataplan],
)

recommendation_agent = Agent(
    model=AGENT_MODEL,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=RECOMMENDATION_INSTRUCTION,
    name="recommendation_agent",
    tools=[check_entitlement],
)

service_agent = Agent(
    model=AGENT_MODEL,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=SERVICE_INSTRUCTION,
    name="service_agent",
    tools=[check_entitlement],
)
root_agent = Agent(
    name="root_agent",
    model=AGENT_MODEL,
    instruction=ORCHESTRATOR_INSTRUCTION,
    global_instruction=GLOBAL_INSTRUCTION,
    sub_agents=[action_agent, recommendation_agent, service_agent],
    tools=[check_entitlement],
)

app = App(root_agent=root_agent, name="app")
