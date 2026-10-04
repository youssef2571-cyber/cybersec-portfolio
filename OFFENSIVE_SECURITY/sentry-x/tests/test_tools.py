from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from sentryx.tools import (
    check_tool_availability,
    run_all,
    run_curl_headers,
    run_dig,
    run_nikto,
    run_nmap,
    run_whatweb,
    run_whois,
)
from sentryx.validators import InvalidTargetError


def _mock_completed_process(stdout: str = "ok", stderr: str = "", returncode: int = 0):
    proc = MagicMock()
    proc.stdout = stdout
    proc.stderr = stderr
    proc.returncode = returncode
    return proc


class TestRunNmap:
    @patch("sentryx.tools.subprocess.run")
    def test_success_builds_correct_argv(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _mock_completed_process("<xml/>")
        result = run_nmap("192.168.1.1", ports="80,443")
        argv = mock_run.call_args.args[0]
        assert argv[0] == "nmap"
        assert "-sV" in argv
        assert "-p" in argv and "80,443" in argv
        assert "192.168.1.1" in argv
        assert result.success is True
        assert result.tool == "nmap"

    @patch("sentryx.tools.subprocess.run")
    def test_os_detection_flag_included_when_requested(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _mock_completed_process()
        run_nmap("192.168.1.1", os_detection=True)
        argv = mock_run.call_args.args[0]
        assert "-O" in argv

    def test_invalid_target_rejected_before_subprocess_call(self) -> None:
        with pytest.raises(InvalidTargetError):
            run_nmap("--script=foo")

    @patch("sentryx.tools.subprocess.run")
    def test_nonzero_exit_marks_failure_not_exception(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _mock_completed_process(stderr="error", returncode=1)
        result = run_nmap("192.168.1.1")
        assert result.success is False
        assert "exit code 1" in result.error

    @patch("sentryx.tools.subprocess.run")
    def test_timeout_captured_as_result_not_raised(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="nmap", timeout=5)
        result = run_nmap("192.168.1.1", timeout_seconds=5)
        assert result.success is False
        assert "timed out" in result.error

    @patch("sentryx.tools.subprocess.run")
    def test_binary_not_found_captured_as_result(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = FileNotFoundError()
        result = run_nmap("192.168.1.1")
        assert result.success is False
        assert "binary not found" in result.error


class TestOtherTools:
    @patch("sentryx.tools.subprocess.run")
    def test_whois(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _mock_completed_process("domain info")
        result = run_whois("example.com")
        assert mock_run.call_args.args[0] == ["whois", "example.com"]
        assert result.success is True

    @patch("sentryx.tools.subprocess.run")
    def test_whatweb(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _mock_completed_process("{}")
        run_whatweb("example.com")
        argv = mock_run.call_args.args[0]
        assert argv[0] == "whatweb"
        assert "example.com" in argv

    @patch("sentryx.tools.subprocess.run")
    def test_dig_invalid_record_type_falls_back_to_any(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _mock_completed_process()
        run_dig("example.com", record_type="NOT_A_TYPE")
        argv = mock_run.call_args.args[0]
        assert "ANY" in argv

    @patch("sentryx.tools.subprocess.run")
    def test_curl_headers_uses_https_by_default(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _mock_completed_process()
        run_curl_headers("example.com")
        argv = mock_run.call_args.args[0]
        assert "https://example.com" in argv

    @patch("sentryx.tools.subprocess.run")
    def test_curl_headers_http_when_requested(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _mock_completed_process()
        run_curl_headers("example.com", use_https=False)
        argv = mock_run.call_args.args[0]
        assert "http://example.com" in argv

    def test_nikto_rejects_invalid_port(self) -> None:
        with pytest.raises(ValueError):
            run_nikto("example.com", port=99999)


class TestRunAll:
    @patch("sentryx.tools.subprocess.run")
    def test_runs_five_tools_by_default(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _mock_completed_process()
        results = run_all("example.com")
        assert len(results) == 5
        assert {r.tool for r in results} == {"nmap", "whois", "whatweb", "dig", "curl_headers"}

    @patch("sentryx.tools.subprocess.run")
    def test_includes_nikto_when_requested(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _mock_completed_process()
        results = run_all("example.com", include_nikto=True)
        assert len(results) == 6
        assert "nikto" in {r.tool for r in results}

    def test_invalid_target_fails_fast_no_subprocess_calls(self) -> None:
        with patch("sentryx.tools.subprocess.run") as mock_run:
            with pytest.raises(InvalidTargetError):
                run_all("; rm -rf /")
            mock_run.assert_not_called()


class TestCheckToolAvailability:
    def test_returns_bool_for_every_required_binary(self) -> None:
        availability = check_tool_availability()
        from sentryx.tools import REQUIRED_BINARIES

        assert set(availability.keys()) == set(REQUIRED_BINARIES)
        assert all(isinstance(v, bool) for v in availability.values())
