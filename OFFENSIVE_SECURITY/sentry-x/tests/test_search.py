from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from sentryx.search import NVDError, rate_limited_search, search_cves_by_keyword

SAMPLE_NVD_RESPONSE = {
    "vulnerabilities": [
        {
            "cve": {
                "id": "CVE-2021-41773",
                "descriptions": [{"lang": "en", "value": "Path traversal in Apache 2.4.49"}],
                "metrics": {
                    "cvssMetricV31": [{"cvssData": {"baseScore": 7.5, "baseSeverity": "HIGH"}}]
                },
                "published": "2021-10-05T00:00Z",
            }
        }
    ]
}


class TestSearchCvesByKeyword:
    def test_empty_keyword_returns_empty_list_no_request(self) -> None:
        session = MagicMock()
        assert search_cves_by_keyword("", session=session) == []
        session.get.assert_not_called()

    def test_parses_valid_response(self) -> None:
        session = MagicMock()
        resp = MagicMock()
        resp.json.return_value = SAMPLE_NVD_RESPONSE
        resp.raise_for_status.return_value = None
        session.get.return_value = resp

        results = search_cves_by_keyword("Apache 2.4.49", session=session)
        assert len(results) == 1
        assert results[0].cve_id == "CVE-2021-41773"
        assert results[0].cvss_score == 7.5
        assert results[0].severity == "HIGH"

    def test_request_exception_raises_nvd_error(self) -> None:
        session = MagicMock()
        session.get.side_effect = requests.ConnectionError("no route to host")
        with pytest.raises(NVDError, match="NVD request failed"):
            search_cves_by_keyword("whatever", session=session)

    def test_http_error_status_raises_nvd_error(self) -> None:
        session = MagicMock()
        resp = MagicMock()
        resp.raise_for_status.side_effect = requests.HTTPError("429")
        session.get.return_value = resp
        with pytest.raises(NVDError):
            search_cves_by_keyword("whatever", session=session)

    def test_api_key_passed_as_header(self) -> None:
        session = MagicMock()
        resp = MagicMock()
        resp.json.return_value = {"vulnerabilities": []}
        resp.raise_for_status.return_value = None
        session.get.return_value = resp

        search_cves_by_keyword("x", api_key="secret123", session=session)
        _, kwargs = session.get.call_args
        assert kwargs["headers"] == {"apiKey": "secret123"}

    def test_no_matches_returns_empty_list(self) -> None:
        session = MagicMock()
        resp = MagicMock()
        resp.json.return_value = {"vulnerabilities": []}
        resp.raise_for_status.return_value = None
        session.get.return_value = resp
        assert search_cves_by_keyword("nonexistent-thing-xyz", session=session) == []


class TestRateLimitedSearch:
    @patch("sentryx.search.time.sleep")
    def test_sleeps_between_calls_not_before_first(self, mock_sleep: MagicMock) -> None:
        session = MagicMock()
        resp = MagicMock()
        resp.json.return_value = {"vulnerabilities": []}
        resp.raise_for_status.return_value = None
        session.get.return_value = resp

        results = rate_limited_search(["a", "b", "c"], session=session)
        assert len(results) == 3
        assert mock_sleep.call_count == 2  # not before the first call

    @patch("sentryx.search.time.sleep")
    def test_individual_failure_does_not_abort_batch(self, mock_sleep: MagicMock) -> None:
        session = MagicMock()
        ok_resp = MagicMock()
        ok_resp.json.return_value = {"vulnerabilities": []}
        ok_resp.raise_for_status.return_value = None
        session.get.side_effect = [requests.ConnectionError("down"), ok_resp]

        results = rate_limited_search(["bad", "good"], session=session)
        assert results["bad"] == []
        assert results["good"] == []  # empty but not raised
