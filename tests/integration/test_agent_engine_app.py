"""Integration tests for the deprecated Agent Engine entrypoint were removed."""

import pytest


@pytest.mark.skip(reason="Agent Engine deployment removed; Cloud Run app is now the entrypoint")
def test_agent_engine_removed() -> None:
    assert True
