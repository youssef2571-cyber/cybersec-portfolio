"""
Integration tests for sentryx.db.Database.

These run against a REAL PostgreSQL instance (not mocked) - the migration's
correctness and the query logic's correctness are both exercised honestly.

Requires env vars SENTRYX_DB_* pointing at a disposable test database (see
scripts/run_tests.sh / CI workflow for how this is provisioned). Tests are
skipped automatically if the DB is unreachable, so `pytest` still runs
cleanly on a machine without PostgreSQL (e.g. a contributor's laptop running
only unit tests).
"""

from __future__ import annotations

import os

import psycopg2
import pytest

from sentryx.config import Settings
from sentryx.db import Database

TEST_DB_SETTINGS = Settings(
    db_host=os.environ.get("SENTRYX_TEST_DB_HOST", "localhost"),
    db_port=int(os.environ.get("SENTRYX_TEST_DB_PORT", "5432")),
    db_name=os.environ.get("SENTRYX_TEST_DB_NAME", "sentryx_test"),
    db_user=os.environ.get("SENTRYX_TEST_DB_USER", "sentryx_test"),
    db_password=os.environ.get("SENTRYX_TEST_DB_PASSWORD", "testpass123"),
    anthropic_api_key="unused-in-db-tests",
    anthropic_model="unused",
    tool_timeout_seconds=1,
    max_agentic_turns=1,
    nvd_api_key=None,
    log_level="INFO",
)


def _db_reachable() -> bool:
    try:
        conn = psycopg2.connect(
            host=TEST_DB_SETTINGS.db_host,
            port=TEST_DB_SETTINGS.db_port,
            dbname=TEST_DB_SETTINGS.db_name,
            user=TEST_DB_SETTINGS.db_user,
            password=TEST_DB_SETTINGS.db_password,
            connect_timeout=2,
        )
        conn.close()
        return True
    except psycopg2.OperationalError:
        return False


pytestmark = pytest.mark.skipif(
    not _db_reachable(), reason="Test PostgreSQL database not reachable"
)


@pytest.fixture
def db():
    database = Database(TEST_DB_SETTINGS)
    yield database
    # Clean up every table between tests so tests stay independent.
    with database._cursor() as cur:  # noqa: SLF001 - test-only cleanup, not prod code path
        cur.execute("TRUNCATE scan_sessions CASCADE")
    database.close()


class TestScanSessions:
    def test_create_and_get_session(self, db: Database) -> None:
        session_id = db.create_session("example.com", "Youssef", "TICKET-1")
        session = db.get_session(session_id)
        assert session is not None
        assert session.target == "example.com"
        assert session.authorized_by == "Youssef"
        assert session.status == "active"

    def test_get_nonexistent_session_returns_none(self, db: Database) -> None:
        assert db.get_session(999999) is None

    def test_set_session_status(self, db: Database) -> None:
        session_id = db.create_session("example.com")
        db.set_session_status(session_id, "completed")
        assert db.get_session(session_id).status == "completed"

    def test_list_sessions_orders_newest_first(self, db: Database) -> None:
        id1 = db.create_session("first.com")
        id2 = db.create_session("second.com")
        sessions = db.list_sessions()
        ids_in_order = [s["id"] for s in sessions]
        assert ids_in_order.index(id2) < ids_in_order.index(id1)

    def test_delete_session_cascades_to_children(self, db: Database) -> None:
        session_id = db.create_session("example.com")
        vuln_id = db.save_vulnerability(session_id, "Test vuln", "low")
        db.save_fix(vuln_id, "Fix it")

        db.delete_session(session_id)

        assert db.get_session(session_id) is None
        assert db.get_vulnerabilities(session_id) == []


class TestToolRuns:
    def test_save_and_retrieve_tool_run(self, db: Database) -> None:
        session_id = db.create_session("example.com")
        db.save_tool_run(session_id, "nmap", True, 1.5, "22/tcp open", None)
        runs = db.get_tool_runs(session_id)
        assert len(runs) == 1
        assert runs[0]["tool_name"] == "nmap"
        assert runs[0]["success"] is True

    def test_failed_tool_run_stores_error(self, db: Database) -> None:
        session_id = db.create_session("example.com")
        db.save_tool_run(session_id, "nikto", False, 0.1, "", "timed out after 600s")
        runs = db.get_tool_runs(session_id)
        assert runs[0]["success"] is False
        assert runs[0]["error"] == "timed out after 600s"


class TestVulnerabilitiesAndFixes:
    def test_save_vulnerability_and_fix(self, db: Database) -> None:
        session_id = db.create_session("example.com")
        vuln_id = db.save_vulnerability(
            session_id,
            "Outdated Apache",
            "high",
            cve_id="CVE-2021-41773",
            cvss_score=7.5,
            port="443",
            service="https",
            description="Path traversal",
        )
        db.save_fix(vuln_id, "Upgrade Apache")

        vulns = db.get_vulnerabilities(session_id)
        assert len(vulns) == 1
        assert vulns[0]["cve_id"] == "CVE-2021-41773"

        fixes = db.get_fixes_for_session(session_id)
        assert fixes[vuln_id][0]["fix_text"] == "Upgrade Apache"

    def test_vulnerabilities_sorted_by_cvss_desc(self, db: Database) -> None:
        session_id = db.create_session("example.com")
        db.save_vulnerability(session_id, "Low issue", "low", cvss_score=2.0)
        db.save_vulnerability(session_id, "Critical issue", "critical", cvss_score=9.8)
        vulns = db.get_vulnerabilities(session_id)
        assert vulns[0]["vuln_name"] == "Critical issue"

    def test_invalid_severity_rejected_by_check_constraint(self, db: Database) -> None:
        session_id = db.create_session("example.com")
        with pytest.raises(psycopg2.errors.CheckViolation):
            db.save_vulnerability(session_id, "Bad severity", "not_a_real_severity")

    def test_delete_vulnerability_cascades_to_fixes(self, db: Database) -> None:
        session_id = db.create_session("example.com")
        vuln_id = db.save_vulnerability(session_id, "Test", "low")
        db.save_fix(vuln_id, "Fix")
        db.delete_vulnerability(vuln_id)
        fixes = db.get_fixes_for_vulnerability(vuln_id)
        assert fixes == []


class TestSummariesAndApiUsage:
    def test_save_summary(self, db: Database) -> None:
        session_id = db.create_session("example.com")
        db.save_summary(
            session_id,
            raw_scan_json='{"ok": true}',
            ai_analysis="Looks fine.",
            risk_level="low",
            model_used="claude-sonnet-4-6",
            input_tokens=100,
            output_tokens=50,
        )
        # No dedicated getter was specced for summaries in the CLI yet;
        # verify via raw query that the row landed correctly.
        with db._cursor() as cur:  # noqa: SLF001
            cur.execute("SELECT * FROM ai_summaries WHERE session_id = %s", (session_id,))
            row = cur.fetchone()
        assert row["risk_level"] == "low"
        assert row["input_tokens"] == 100

    def test_log_api_usage(self, db: Database) -> None:
        session_id = db.create_session("example.com")
        db.log_api_usage(session_id, "claude-sonnet-4-6", 200, 100, 0.0042)
        with db._cursor() as cur:  # noqa: SLF001
            cur.execute("SELECT * FROM api_usage WHERE session_id = %s", (session_id,))
            row = cur.fetchone()
        assert row["input_tokens"] == 200
        assert float(row["estimated_cost_usd"]) == pytest.approx(0.0042)

    def test_api_usage_survives_session_deletion(self, db: Database) -> None:
        """api_usage.session_id is ON DELETE SET NULL (not CASCADE) - cost
        tracking should outlive the session it was spent on."""
        session_id = db.create_session("example.com")
        db.log_api_usage(session_id, "claude-sonnet-4-6", 200, 100, 0.0042)
        db.delete_session(session_id)
        with db._cursor() as cur:  # noqa: SLF001
            cur.execute("SELECT * FROM api_usage")
            rows = cur.fetchall()
        assert len(rows) == 1
        assert rows[0]["session_id"] is None
