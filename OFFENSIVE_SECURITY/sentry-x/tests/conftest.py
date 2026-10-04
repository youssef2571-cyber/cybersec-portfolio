from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Ensure tests never accidentally pick up real secrets from the host
    environment - every test that needs config sets it explicitly."""
    for var in (
        "ANTHROPIC_API_KEY",
        "SENTRYX_DB_USER",
        "SENTRYX_DB_PASSWORD",
        "SENTRYX_DB_HOST",
        "SENTRYX_DB_PORT",
        "SENTRYX_DB_NAME",
    ):
        monkeypatch.delenv(var, raising=False)
    yield
