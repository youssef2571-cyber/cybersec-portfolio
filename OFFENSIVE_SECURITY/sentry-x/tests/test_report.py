from __future__ import annotations

from datetime import datetime

from sentryx.report import render_html_report

SESSION = {
    "target": "example.com",
    "scan_date": datetime(2026, 1, 1, 12, 0),
    "authorization_ref": "TICKET-123",
}


class TestRenderHtmlReport:
    def test_basic_report_contains_target_and_findings(self) -> None:
        vulns = [
            {
                "id": 1,
                "vuln_name": "Outdated Apache",
                "severity": "high",
                "cve_id": "CVE-2021-41773",
                "port": "443",
                "service": "https",
                "description": "Path traversal vulnerability.",
            }
        ]
        fixes = {1: [{"fix_text": "Upgrade to Apache 2.4.51 or later."}]}
        html_out = render_html_report(SESSION, vulns, fixes, None)

        assert "example.com" in html_out
        assert "Outdated Apache" in html_out
        assert "CVE-2021-41773" in html_out
        assert "Upgrade to Apache 2.4.51" in html_out
        assert "HIGH" in html_out
        assert "TICKET-123" in html_out

    def test_empty_findings_shows_placeholder_row(self) -> None:
        html_out = render_html_report(SESSION, [], {}, None)
        assert "No findings recorded" in html_out

    def test_html_is_escaped_against_injection(self) -> None:
        vulns = [
            {
                "id": 1,
                "vuln_name": "<script>alert(1)</script>",
                "severity": "low",
                "cve_id": None,
                "port": None,
                "service": None,
                "description": "test",
            }
        ]
        html_out = render_html_report(SESSION, vulns, {}, None)
        assert "<script>alert(1)</script>" not in html_out
        assert "&lt;script&gt;" in html_out

    def test_findings_sorted_by_severity_critical_first(self) -> None:
        vulns = [
            {
                "id": 1,
                "vuln_name": "Low issue",
                "severity": "low",
                "cve_id": None,
                "port": None,
                "service": None,
                "description": "d",
            },
            {
                "id": 2,
                "vuln_name": "Critical issue",
                "severity": "critical",
                "cve_id": None,
                "port": None,
                "service": None,
                "description": "d",
            },
        ]
        html_out = render_html_report(SESSION, vulns, {}, None)
        assert html_out.index("Critical issue") < html_out.index("Low issue")

    def test_ai_summary_included_when_provided(self) -> None:
        summary = {"risk_level": "high", "ai_analysis": "Overall posture is weak."}
        html_out = render_html_report(SESSION, [], {}, summary)
        assert "Executive Summary" in html_out
        assert "Overall posture is weak." in html_out
        assert "HIGH" in html_out

    def test_missing_authorization_ref_flagged(self) -> None:
        session = dict(SESSION)
        session["authorization_ref"] = None
        html_out = render_html_report(session, [], {}, None)
        assert "NOT RECORDED" in html_out
