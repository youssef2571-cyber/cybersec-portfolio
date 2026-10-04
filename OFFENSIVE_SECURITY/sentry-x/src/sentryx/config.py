#!/usr/bin/env python3
"""
sentryx.config
---------------
Centralized configuration loaded from environment variables (.env in dev).
No secret ever has a hardcoded default - missing required secrets raise at
startup rather than silently falling back to an insecure default.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()  # no-op in prod if no .env file is present


class MissingConfigError(RuntimeError):
    pass


def _require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise MissingConfigError(
            f"Required environment variable '{name}' is not set. "
            f"Copy .env.example to .env and fill it in."
        )
    return val


def _optional(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    # Database
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    # Anthropic API
    anthropic_api_key: str
    anthropic_model: str

    # Tool behavior
    tool_timeout_seconds: int
    max_agentic_turns: int
    nvd_api_key: str | None

    # Logging
    log_level: str


def load_settings(require_llm: bool = True, require_db: bool = True) -> Settings:
    """
    Load settings from the environment. By default requires both the LLM
    key and DB credentials; callers that only need one subsystem (e.g. unit
    tests exercising tools.py in isolation) can set the relevant flag False.
    """
    return Settings(
        db_host=_optional("SENTRYX_DB_HOST", "localhost"),
        db_port=int(_optional("SENTRYX_DB_PORT", "5432")),
        db_name=_optional("SENTRYX_DB_NAME", "sentryx"),
        db_user=(_require("SENTRYX_DB_USER") if require_db else _optional("SENTRYX_DB_USER", "")),
        db_password=(
            _require("SENTRYX_DB_PASSWORD") if require_db else _optional("SENTRYX_DB_PASSWORD", "")
        ),
        anthropic_api_key=(
            _require("ANTHROPIC_API_KEY") if require_llm else _optional("ANTHROPIC_API_KEY", "")
        ),
        anthropic_model=_optional("SENTRYX_MODEL", "claude-sonnet-4-6"),
        tool_timeout_seconds=int(_optional("SENTRYX_TOOL_TIMEOUT", "120")),
        max_agentic_turns=int(_optional("SENTRYX_MAX_AGENTIC_TURNS", "6")),
        nvd_api_key=os.environ.get("NVD_API_KEY"),  # optional, raises your NVD rate limit
        log_level=_optional("SENTRYX_LOG_LEVEL", "INFO"),
    )
