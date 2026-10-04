from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import anthropic
import pytest

from sentryx.llm import AnalysisError, analyze_scan
from sentryx.tools import ToolResult


def _tool_results() -> list[ToolResult]:
    return [
        ToolResult(
            tool="nmap",
            target="example.com",
            success=True,
            duration_seconds=1.2,
            raw_output="22/tcp open ssh",
        )
    ]


def _text_block(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _usage(input_tokens: int = 100, output_tokens: int = 50):
    u = MagicMock()
    u.input_tokens = input_tokens
    u.output_tokens = output_tokens
    return u


class TestAnalyzeScanHappyPath:
    @patch("sentryx.llm.anthropic.Anthropic")
    def test_single_turn_valid_json_response(self, mock_anthropic_cls: MagicMock) -> None:
        final_json = json.dumps(
            {
                "risk_level": "medium",
                "summary": "SSH exposed with default config.",
                "findings": [
                    {
                        "vuln_name": "Open SSH port",
                        "severity": "medium",
                        "port": "22",
                        "service": "ssh",
                        "description": "SSH is reachable from the internet.",
                        "remediation": "Restrict via firewall / use key auth only.",
                    }
                ],
            }
        )
        mock_response = MagicMock()
        mock_response.content = [_text_block(final_json)]
        mock_response.usage = _usage()

        client = MagicMock()
        client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = client

        result = analyze_scan(
            api_key="fake-key",
            model="claude-sonnet-4-6",
            target="example.com",
            tool_results=_tool_results(),
        )

        assert result.risk_level == "medium"
        assert len(result.findings) == 1
        assert result.findings[0]["vuln_name"] == "Open SSH port"
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.additional_tool_calls == []

    @patch("sentryx.llm.anthropic.Anthropic")
    def test_strips_markdown_fences_from_response(self, mock_anthropic_cls: MagicMock) -> None:
        final_json = (
            "```json\n"
            + json.dumps(
                {
                    "risk_level": "low",
                    "summary": "ok",
                    "findings": [],
                }
            )
            + "\n```"
        )
        mock_response = MagicMock()
        mock_response.content = [_text_block(final_json)]
        mock_response.usage = _usage()
        client = MagicMock()
        client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = client

        result = analyze_scan("key", "model", "example.com", _tool_results())
        assert result.risk_level == "low"


class TestAnalyzeScanToolUseLoop:
    @patch("sentryx.llm.anthropic.Anthropic")
    @patch("sentryx.llm.TOOL_REGISTRY")
    def test_model_requests_additional_tool_then_converges(
        self, mock_registry: MagicMock, mock_anthropic_cls: MagicMock
    ) -> None:
        extra_result = ToolResult(
            tool="nikto",
            target="example.com",
            success=True,
            duration_seconds=5.0,
            raw_output="no issues found",
        )
        fake_tool_fn = MagicMock(return_value=extra_result)
        mock_registry.get.return_value = fake_tool_fn
        mock_registry.keys.return_value = ["nmap", "nikto"]

        tool_use_block = MagicMock()
        tool_use_block.type = "tool_use"
        tool_use_block.id = "tu_1"
        tool_use_block.input = {"tool": "nikto", "reason": "web server found"}

        turn1_response = MagicMock()
        turn1_response.content = [tool_use_block]
        turn1_response.usage = _usage()

        final_json = json.dumps({"risk_level": "info", "summary": "clean", "findings": []})
        turn2_response = MagicMock()
        turn2_response.content = [_text_block(final_json)]
        turn2_response.usage = _usage()

        client = MagicMock()
        client.messages.create.side_effect = [turn1_response, turn2_response]
        mock_anthropic_cls.return_value = client

        result = analyze_scan("key", "model", "example.com", _tool_results(), max_turns=6)

        assert result.risk_level == "info"
        assert len(result.additional_tool_calls) == 1
        assert result.additional_tool_calls[0]["tool"] == "nikto"
        fake_tool_fn.assert_called_once_with("example.com")


class TestAnalyzeScanErrors:
    @patch("sentryx.llm.anthropic.Anthropic")
    def test_invalid_json_raises_analysis_error(self, mock_anthropic_cls: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.content = [_text_block("not valid json at all")]
        mock_response.usage = _usage()
        client = MagicMock()
        client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = client

        with pytest.raises(AnalysisError, match="not valid JSON"):
            analyze_scan("key", "model", "example.com", _tool_results())

    @patch("sentryx.llm.anthropic.Anthropic")
    def test_missing_required_key_raises_analysis_error(
        self, mock_anthropic_cls: MagicMock
    ) -> None:
        bad_json = json.dumps({"risk_level": "low"})  # missing summary/findings
        mock_response = MagicMock()
        mock_response.content = [_text_block(bad_json)]
        mock_response.usage = _usage()
        client = MagicMock()
        client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = client

        with pytest.raises(AnalysisError, match="missing required key"):
            analyze_scan("key", "model", "example.com", _tool_results())

    @patch("sentryx.llm.anthropic.Anthropic")
    def test_api_error_wrapped_as_analysis_error(self, mock_anthropic_cls: MagicMock) -> None:
        client = MagicMock()
        client.messages.create.side_effect = anthropic.APIError(
            message="boom", request=MagicMock(), body=None
        )
        mock_anthropic_cls.return_value = client

        with pytest.raises(AnalysisError, match="Anthropic API error"):
            analyze_scan("key", "model", "example.com", _tool_results())

    @patch("sentryx.llm.anthropic.Anthropic")
    def test_never_converging_raises_after_max_turns(self, mock_anthropic_cls: MagicMock) -> None:
        tool_use_block = MagicMock()
        tool_use_block.type = "tool_use"
        tool_use_block.id = "tu_x"
        tool_use_block.input = {"tool": "unknown_tool", "reason": "x"}

        response = MagicMock()
        response.content = [tool_use_block]
        response.usage = _usage()

        client = MagicMock()
        client.messages.create.return_value = response
        mock_anthropic_cls.return_value = client

        with pytest.raises(AnalysisError, match="did not converge"):
            analyze_scan("key", "model", "example.com", _tool_results(), max_turns=2)
        assert client.messages.create.call_count == 2
