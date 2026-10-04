from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from sentryx.cli import cli


class TestCheckCommand:
    @patch("sentryx.cli.check_tool_availability")
    def test_all_tools_present_exits_zero(self, mock_check: MagicMock) -> None:
        mock_check.return_value = {
            t: True for t in ["nmap", "whois", "whatweb", "dig", "curl", "nikto"]
        }
        result = CliRunner().invoke(cli, ["check"])
        assert result.exit_code == 0

    @patch("sentryx.cli.check_tool_availability")
    def test_missing_tool_exits_nonzero(self, mock_check: MagicMock) -> None:
        mock_check.return_value = {
            "nmap": True,
            "whois": False,
            "whatweb": True,
            "dig": True,
            "curl": True,
            "nikto": True,
        }
        result = CliRunner().invoke(cli, ["check"])
        assert result.exit_code == 1


class TestScanCommandValidation:
    def test_invalid_target_rejected_before_any_db_or_api_call(self) -> None:
        with patch("sentryx.cli.load_settings") as mock_settings:
            result = CliRunner().invoke(
                cli, ["scan", "--target", "; rm -rf /", "--authorization-ref", "T-1"]
            )
            assert result.exit_code == 1
            mock_settings.assert_not_called()

    def test_missing_config_reports_clear_error(self) -> None:
        from sentryx.config import MissingConfigError

        with patch(
            "sentryx.cli.load_settings", side_effect=MissingConfigError("ANTHROPIC_API_KEY missing")
        ):
            result = CliRunner().invoke(
                cli, ["scan", "--target", "example.com", "--authorization-ref", "T-1"]
            )
            assert result.exit_code == 1
            assert "ANTHROPIC_API_KEY missing" in result.output

    def test_no_authorization_ref_prompts_for_confirmation(self) -> None:
        result = CliRunner().invoke(cli, ["scan", "--target", "example.com"], input="n\n")
        assert result.exit_code == 1
        assert "Continue without an authorization reference" in result.output


class TestScanCommandSkipAi:
    @patch("sentryx.cli.Database")
    @patch("sentryx.cli.load_settings")
    @patch("sentryx.cli.run_all")
    def test_skip_ai_runs_recon_and_stores_results_without_calling_llm(
        self, mock_run_all: MagicMock, mock_settings: MagicMock, mock_db_cls: MagicMock
    ) -> None:
        from sentryx.tools import ToolResult

        mock_run_all.return_value = [
            ToolResult(
                tool="nmap",
                target="example.com",
                success=True,
                duration_seconds=1.0,
                raw_output="22/tcp open",
            ),
        ]
        settings = MagicMock()
        settings.log_level = "INFO"
        mock_settings.return_value = settings

        db_instance = MagicMock()
        db_instance.create_session.return_value = 1
        mock_db_cls.return_value = db_instance

        with patch("sentryx.cli.analyze_scan") as mock_analyze:
            result = CliRunner().invoke(
                cli,
                ["scan", "--target", "example.com", "--authorization-ref", "T-1", "--skip-ai"],
            )
            assert result.exit_code == 0, result.output
            mock_analyze.assert_not_called()
            db_instance.save_tool_run.assert_called_once()
            db_instance.set_session_status.assert_called_with(1, "completed")


class TestListCommand:
    @patch("sentryx.cli.Database")
    @patch("sentryx.cli.load_settings")
    def test_list_renders_sessions_table(
        self, mock_settings: MagicMock, mock_db_cls: MagicMock
    ) -> None:
        db_instance = MagicMock()
        db_instance.list_sessions.return_value = [
            {
                "id": 1,
                "target": "example.com",
                "scan_date": "2026-01-01",
                "status": "completed",
                "authorization_ref": "T-1",
            }
        ]
        mock_db_cls.return_value = db_instance

        result = CliRunner().invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "example.com" in result.output
        db_instance.close.assert_called_once()
