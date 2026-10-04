#!/usr/bin/env python3
"""
sentryx.search
---------------
CVE lookups against the NVD REST API (api.nist.gov). No API key required,
though providing NVD_API_KEY raises the rate limit from 5 to 50 req/30s.

NOTE: this module makes outbound HTTPS calls at runtime - it is covered by
unit tests using a mocked `requests` session, not live calls, so CI never
depends on nvd.nist.gov being reachable.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import requests

logger = logging.getLogger("sentryx.search")

NVD_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
DEFAULT_TIMEOUT = 15


@dataclass
class CVEMatch:
    cve_id: str
    description: str
    cvss_score: float | None
    severity: str | None
    published: str | None


class NVDError(RuntimeError):
    pass


def search_cves_by_keyword(
    keyword: str,
    api_key: str | None = None,
    max_results: int = 5,
    session: requests.Session | None = None,
) -> list[CVEMatch]:
    """
    Search NVD for CVEs matching a free-text keyword (e.g. 'Apache 2.4.49').
    Returns an empty list on no matches - raises NVDError only on a genuine
    transport/parsing failure, so callers can distinguish "no known CVEs"
    from "lookup failed".
    """
    if not keyword or not keyword.strip():
        return []

    sess = session or requests.Session()
    headers = {"apiKey": api_key} if api_key else {}
    params: dict[str, str | int] = {
        "keywordSearch": keyword.strip(),
        "resultsPerPage": max_results,
    }

    try:
        resp = sess.get(NVD_BASE_URL, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        raise NVDError(f"NVD request failed: {exc}") from exc
    except ValueError as exc:
        raise NVDError(f"NVD returned non-JSON response: {exc}") from exc

    return _parse_nvd_response(data)


def _parse_nvd_response(data: dict[str, Any]) -> list[CVEMatch]:
    matches: list[CVEMatch] = []
    for item in data.get("vulnerabilities", []):
        cve = item.get("cve", {})
        cve_id = cve.get("id", "UNKNOWN")

        descriptions = cve.get("descriptions", [])
        description = next((d["value"] for d in descriptions if d.get("lang") == "en"), "")

        cvss_score = None
        severity = None
        metrics = cve.get("metrics", {})
        for metric_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            if metric_key in metrics and metrics[metric_key]:
                cvss_data = metrics[metric_key][0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                severity = cvss_data.get("baseSeverity") or metrics[metric_key][0].get(
                    "baseSeverity"
                )
                break

        matches.append(
            CVEMatch(
                cve_id=cve_id,
                description=description,
                cvss_score=cvss_score,
                severity=severity,
                published=cve.get("published"),
            )
        )
    return matches


def rate_limited_search(
    keywords: list[str],
    api_key: str | None = None,
    session: requests.Session | None = None,
) -> dict[str, list[CVEMatch]]:
    """
    Search multiple keywords while respecting NVD's rate limit: without a
    key, 5 requests per rolling 30s window - we sleep conservatively between
    calls rather than tracking a rolling window precisely.
    """
    delay = 0.6 if api_key else 6.5
    results: dict[str, list[CVEMatch]] = {}
    for i, kw in enumerate(keywords):
        if i > 0:
            time.sleep(delay)
        try:
            results[kw] = search_cves_by_keyword(kw, api_key=api_key, session=session)
        except NVDError as exc:
            logger.warning("CVE lookup failed for '%s': %s", kw, exc)
            results[kw] = []
    return results
