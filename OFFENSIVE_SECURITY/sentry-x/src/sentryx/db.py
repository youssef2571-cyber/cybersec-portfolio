#!/usr/bin/env python3
"""
sentryx.db
-----------
PostgreSQL access layer. Every query is parameterized (psycopg2 placeholders,
never string formatting) - no SQL injection surface, including for fields
that originate from AI output (vuln_name, description, etc.) since that
output is still untrusted input from this application's point of view.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterator

import psycopg2
import psycopg2.extras

from .config import Settings


@dataclass
class ScanSession:
    id: int
    target: str
    scan_date: datetime
    status: str
    authorized_by: str | None
    authorization_ref: str | None
    notes: str | None


class Database:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            dbname=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
        )
        self._conn.autocommit = False

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def _cursor(self) -> Iterator[psycopg2.extras.DictCursor]:
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cur.close()

    # ---- scan_sessions ----------------------------------------------

    def create_session(
        self,
        target: str,
        authorized_by: str | None = None,
        authorization_ref: str | None = None,
    ) -> int:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO scan_sessions (target, authorized_by, authorization_ref)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (target, authorized_by, authorization_ref),
            )
            return cur.fetchone()["id"]

    def set_session_status(self, session_id: int, status: str) -> None:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE scan_sessions SET status = %s WHERE id = %s",
                (status, session_id),
            )

    def get_session(self, session_id: int) -> ScanSession | None:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM scan_sessions WHERE id = %s", (session_id,))
            row = cur.fetchone()
            return ScanSession(**row) if row else None

    def list_sessions(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM scan_sessions ORDER BY scan_date DESC LIMIT %s",
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]

    def delete_session(self, session_id: int) -> None:
        # ON DELETE CASCADE handles children (tool_runs, vulnerabilities, etc.)
        with self._cursor() as cur:
            cur.execute("DELETE FROM scan_sessions WHERE id = %s", (session_id,))

    # ---- tool_runs ----------------------------------------------------

    def save_tool_run(
        self,
        session_id: int,
        tool_name: str,
        success: bool,
        duration_seconds: float,
        raw_output: str,
        error: str | None,
    ) -> int:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO tool_runs
                    (session_id, tool_name, success, duration_seconds, raw_output, error)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (session_id, tool_name, success, duration_seconds, raw_output, error),
            )
            return cur.fetchone()["id"]

    def get_tool_runs(self, session_id: int) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM tool_runs WHERE session_id = %s ORDER BY ran_at",
                (session_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    # ---- vulnerabilities / fixes ---------------------------------------

    def save_vulnerability(
        self,
        session_id: int,
        vuln_name: str,
        severity: str,
        cve_id: str | None = None,
        cvss_score: float | None = None,
        port: str | None = None,
        service: str | None = None,
        description: str | None = None,
        source: str = "ai_analysis",
    ) -> int:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO vulnerabilities
                    (session_id, vuln_name, cve_id, severity, cvss_score,
                     port, service, description, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    session_id,
                    vuln_name,
                    cve_id,
                    severity,
                    cvss_score,
                    port,
                    service,
                    description,
                    source,
                ),
            )
            return cur.fetchone()["id"]

    def save_fix(self, vulnerability_id: int, fix_text: str, source: str = "ai_analysis") -> int:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO fixes (vulnerability_id, fix_text, source)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (vulnerability_id, fix_text, source),
            )
            return cur.fetchone()["id"]

    def get_vulnerabilities(self, session_id: int) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM vulnerabilities WHERE session_id = %s ORDER BY cvss_score DESC NULLS LAST",
                (session_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_fixes_for_vulnerability(self, vulnerability_id: int) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM fixes WHERE vulnerability_id = %s " "ORDER BY created_at",
                (vulnerability_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_fixes_for_session(self, session_id: int) -> dict[int, list[dict[str, Any]]]:
        """Batched version: one query for every vuln in the session instead
        of N+1 per-vulnerability queries."""
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT f.* FROM fixes f
                JOIN vulnerabilities v ON v.id = f.vulnerability_id
                WHERE v.session_id = %s
                ORDER BY f.created_at
                """,
                (session_id,),
            )
            result: dict[int, list[dict[str, Any]]] = {}
            for row in cur.fetchall():
                d = dict(row)
                result.setdefault(d["vulnerability_id"], []).append(d)
            return result

    def delete_vulnerability(self, vulnerability_id: int) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM vulnerabilities WHERE id = %s", (vulnerability_id,))

    # ---- ai_summaries ---------------------------------------------------

    def save_summary(
        self,
        session_id: int,
        raw_scan_json: str,
        ai_analysis: str,
        risk_level: str,
        model_used: str,
        input_tokens: int,
        output_tokens: int,
    ) -> int:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO ai_summaries
                    (session_id, raw_scan_json, ai_analysis, risk_level,
                     model_used, input_tokens, output_tokens)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    session_id,
                    raw_scan_json,
                    ai_analysis,
                    risk_level,
                    model_used,
                    input_tokens,
                    output_tokens,
                ),
            )
            return cur.fetchone()["id"]

    # ---- api_usage ------------------------------------------------------

    def log_api_usage(
        self,
        session_id: int | None,
        model: str,
        input_tokens: int,
        output_tokens: int,
        estimated_cost_usd: float | None,
    ) -> None:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_usage
                    (session_id, model, input_tokens, output_tokens, estimated_cost_usd)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (session_id, model, input_tokens, output_tokens, estimated_cost_usd),
            )
