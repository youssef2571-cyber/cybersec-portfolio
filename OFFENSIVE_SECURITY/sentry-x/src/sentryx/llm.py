#!/usr/bin/env python3
"""
sentryx.llm
------------
Orchestrates analysis via the Anthropic Messages API. The model is given
a tool (`run_recon_tool`) it can call to request additional scans mid-
analysis (e.g. "run nikto on port 8443 after seeing it open in nmap").

Design choices:
  - max_agentic_turns hard-caps the loop so a confused model can't run up
    an unbounded API bill or an unbounded number of scans against a target.
  - Every tool call the model makes is itself re-validated by
    sentryx.validators / sentryx.tools before execution - the model's
    intent is never trusted blindly.
  - Token usage is returned alongside the analysis so the caller can log it
    to api_usage for cost tracking.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, cast

import anthropic

from .tools import TOOL_REGISTRY, ToolResult

logger = logging.getLogger("sentryx.llm")

SYSTEM_PROMPT = """You are a security analyst assistant reviewing reconnaissance \
scan output for an AUTHORIZED penetration test. Written authorization has \
already been confirmed by the operator before this session started - you do \
not need to re-verify that, but you must never suggest or discuss actions \
against targets outside the one provided.

Your job:
1. Review the raw recon output (nmap, whois, whatweb, dig, curl headers, \
   nikto) provided to you.
2. Identify concrete, evidence-based findings. Do not invent vulnerabilities \
   that aren't supported by the scan output - if evidence is thin, say so \
   explicitly rather than guessing.
3. For each finding, give: a short name, a severity (info/low/medium/high/\
   critical), the affected port/service if applicable, a plain-language \
   description, and a concrete remediation step.
4. You may call run_recon_tool to request ONE additional scan if the \
   existing output leaves a specific, important question unanswered (e.g. \
   a web server was found but no nikto scan was run). Do not call it \
   speculatively.
5. When you are done, respond with a JSON object (no markdown fences, no \
   prose outside the JSON) matching this schema:
   {
     "risk_level": "info|low|medium|high|critical",
     "summary": "2-3 sentence executive summary",
     "findings": [
       {
         "vuln_name": "...",
         "severity": "...",
         "port": "...",
         "service": "...",
         "description": "...",
         "remediation": "..."
       }
     ]
   }
"""

TOOL_SCHEMA = {
    "name": "run_recon_tool",
    "description": (
        "Run one additional recon tool against the SAME target already "
        "under analysis. Use sparingly - only when the current evidence "
        "leaves a specific gap."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "tool": {
                "type": "string",
                "enum": list(TOOL_REGISTRY.keys()),
            },
            "reason": {
                "type": "string",
                "description": "Why this additional scan is needed.",
            },
        },
        "required": ["tool", "reason"],
    },
}


@dataclass
class AnalysisResult:
    risk_level: str
    summary: str
    findings: list[dict[str, Any]]
    raw_model_output: str
    input_tokens: int
    output_tokens: int
    additional_tool_calls: list[dict[str, Any]]


class AnalysisError(RuntimeError):
    pass


def analyze_scan(
    api_key: str,
    model: str,
    target: str,
    tool_results: list[ToolResult],
    max_turns: int = 6,
) -> AnalysisResult:
    """
    Run the agentic analysis loop. Returns a structured AnalysisResult.
    Raises AnalysisError if the model never produces parseable JSON within
    max_turns, or if the API call itself fails.
    """
    client = anthropic.Anthropic(api_key=api_key)

    scan_payload = json.dumps([r.to_dict() for r in tool_results], indent=2)
    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": (
                f"Target: {target}\n\nRecon scan results:\n```json\n"
                f"{scan_payload}\n```\n\nAnalyze these results."
            ),
        }
    ]

    total_input_tokens = 0
    total_output_tokens = 0
    additional_calls: list[dict[str, Any]] = []

    for turn in range(max_turns):
        try:
            # The Anthropic SDK's tool/message param types are a large
            # discriminated union that doesn't unify cleanly with a plain
            # dict built at runtime. We validate the shape ourselves
            # (SYSTEM_PROMPT/TOOL_SCHEMA are fixed, messages are built only
            # by this function) rather than hand-maintaining a parallel
            # SDK-typed structure that would drift on every SDK upgrade.
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=cast(Any, [TOOL_SCHEMA]),
                messages=cast(Any, messages),
            )
        except anthropic.APIError as exc:
            raise AnalysisError(f"Anthropic API error: {exc}") from exc

        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        if not tool_use_blocks:
            # Model is done - expect final JSON in the text.
            raw_text = "".join(b.text for b in text_blocks).strip()
            parsed = _parse_final_json(raw_text)
            return AnalysisResult(
                risk_level=parsed["risk_level"],
                summary=parsed["summary"],
                findings=parsed["findings"],
                raw_model_output=raw_text,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                additional_tool_calls=additional_calls,
            )

        # Model wants to run another tool. Execute each requested call
        # (re-validated inside the tool functions themselves) and feed the
        # result back.
        messages.append({"role": "assistant", "content": response.content})
        tool_result_blocks = []
        for block in tool_use_blocks:
            block_input = cast(dict[str, Any], block.input)
            tool_name: str = str(block_input.get("tool", ""))
            reason = block_input.get("reason", "")
            logger.info("Model requested tool=%s reason=%s", tool_name, reason)
            additional_calls.append({"tool": tool_name, "reason": reason, "turn": turn})

            fn = TOOL_REGISTRY.get(tool_name)
            if fn is None:
                result_payload = {"error": f"unknown tool '{tool_name}'"}
            else:
                try:
                    result: ToolResult = fn(target)
                    result_payload = result.to_dict()
                except (
                    Exception
                ) as exc:  # noqa: BLE001 - surfaced to the model, not swallowed silently
                    result_payload = {"error": str(exc)}

            tool_result_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result_payload),
                }
            )
        messages.append({"role": "user", "content": tool_result_blocks})

    raise AnalysisError(f"Model did not converge on a final answer within {max_turns} turns.")


def _parse_final_json(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AnalysisError(
            f"Model output was not valid JSON: {exc}\nOutput was:\n{raw_text}"
        ) from exc

    for key in ("risk_level", "summary", "findings"):
        if key not in parsed:
            raise AnalysisError(f"Model JSON missing required key '{key}'.")
    return parsed
