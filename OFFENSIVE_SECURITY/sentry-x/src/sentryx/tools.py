#!/usr/bin/env python3
"""
sentryx.tools
--------------
Subprocess wrappers around recon tools. Every function:
  - validates its target via sentryx.validators before touching subprocess
  - never uses shell=True
  - passes arguments as a list (no string concatenation into a command line)
  - enforces a timeout
  - returns a structured ToolResult (never raises on tool failure - failures
    are captured in the result so a single failing tool never aborts a scan)

These wrappers assume the underlying binaries (nmap, whois, whatweb, dig,
curl, nikto) are installed on PATH. Call check_tool_availability() at
startup to fail fast with a clear message instead of a confusing subprocess
error mid-scan.
"""

from __future__ import annotations

import json
import shutil
import subprocess  # nosec B404 - required for recon tool execution; see validators.py
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .validators import validate_port_spec, validate_target

REQUIRED_BINARIES = ["nmap", "whois", "whatweb", "dig", "curl", "nikto"]


@dataclass
class ToolResult:
    tool: str
    target: str
    success: bool
    duration_seconds: float
    raw_output: str
    error: str | None = None
    parsed: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "target": self.target,
            "success": self.success,
            "duration_seconds": round(self.duration_seconds, 3),
            "raw_output": self.raw_output,
            "error": self.error,
            "parsed": self.parsed,
        }


def check_tool_availability() -> dict[str, bool]:
    """Return {binary_name: is_on_path} for every required binary."""
    return {name: shutil.which(name) is not None for name in REQUIRED_BINARIES}


def _run(
    tool_name: str,
    target: str,
    argv: list[str],
    timeout_seconds: int,
) -> ToolResult:
    """Shared subprocess execution path for all tool wrappers."""
    start = time.monotonic()
    try:
        # shell=True is never used; argv is always a list built from a
        # target that has already passed validate_target()/
        # validate_port_spec() (see validators.py) before reaching here.
        proc = subprocess.run(  # nosec B603
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        duration = time.monotonic() - start
        output = proc.stdout + (("\n[stderr]\n" + proc.stderr) if proc.stderr else "")
        success = proc.returncode == 0
        return ToolResult(
            tool=tool_name,
            target=target,
            success=success,
            duration_seconds=duration,
            raw_output=output.strip(),
            error=None if success else f"exit code {proc.returncode}",
        )
    except FileNotFoundError:
        return ToolResult(
            tool=tool_name,
            target=target,
            success=False,
            duration_seconds=time.monotonic() - start,
            raw_output="",
            error=f"binary not found on PATH: {argv[0]}",
        )
    except subprocess.TimeoutExpired:
        return ToolResult(
            tool=tool_name,
            target=target,
            success=False,
            duration_seconds=timeout_seconds,
            raw_output="",
            error=f"timed out after {timeout_seconds}s",
        )


def run_nmap(
    target: str,
    ports: str | None = None,
    timeout_seconds: int = 300,
    service_detection: bool = True,
    os_detection: bool = False,
) -> ToolResult:
    t = validate_target(target)
    argv = ["nmap"]
    if service_detection:
        argv.append("-sV")
    if os_detection:
        argv.append("-O")
    if ports:
        argv += ["-p", validate_port_spec(ports)]
    argv += ["-oX", "-", t]  # XML to stdout - machine parseable
    result = _run("nmap", t, argv, timeout_seconds)
    return result


def run_whois(target: str, timeout_seconds: int = 30) -> ToolResult:
    t = validate_target(target)
    return _run("whois", t, ["whois", t], timeout_seconds)


def run_whatweb(target: str, timeout_seconds: int = 60) -> ToolResult:
    t = validate_target(target)
    return _run("whatweb", t, ["whatweb", "--log-json=-", t], timeout_seconds)


def run_dig(target: str, record_type: str = "ANY", timeout_seconds: int = 20) -> ToolResult:
    t = validate_target(target)
    allowed_types = {"A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "ANY"}
    rt = record_type.upper()
    if rt not in allowed_types:
        rt = "ANY"
    return _run("dig", t, ["dig", t, rt, "+noall", "+answer"], timeout_seconds)


def run_curl_headers(target: str, use_https: bool = True, timeout_seconds: int = 20) -> ToolResult:
    t = validate_target(target)
    scheme = "https" if use_https else "http"
    url = f"{scheme}://{t}"
    return _run(
        "curl_headers",
        t,
        ["curl", "-sS", "-I", "--max-time", str(timeout_seconds), url],
        timeout_seconds + 5,
    )


def run_nikto(target: str, port: int = 80, timeout_seconds: int = 600) -> ToolResult:
    t = validate_target(target)
    if not (0 <= port <= 65535):
        raise ValueError(f"Invalid port: {port}")
    return _run(
        "nikto",
        t,
        ["nikto", "-h", t, "-p", str(port), "-Format", "json", "-o", "-"],
        timeout_seconds,
    )


TOOL_REGISTRY: dict[str, Callable[..., ToolResult]] = {
    "nmap": run_nmap,
    "whois": run_whois,
    "whatweb": run_whatweb,
    "dig": run_dig,
    "curl_headers": run_curl_headers,
    "nikto": run_nikto,
}


def run_all(
    target: str, include_nikto: bool = False, timeout_seconds: int = 120
) -> list[ToolResult]:
    """Run the standard recon set against a target. Validates once up front
    so a bad target fails fast instead of failing six times."""
    validate_target(target)
    results = [
        run_nmap(target, timeout_seconds=timeout_seconds),
        run_whois(target, timeout_seconds=min(timeout_seconds, 30)),
        run_whatweb(target, timeout_seconds=min(timeout_seconds, 60)),
        run_dig(target, timeout_seconds=min(timeout_seconds, 20)),
        run_curl_headers(target, timeout_seconds=min(timeout_seconds, 20)),
    ]
    if include_nikto:
        results.append(run_nikto(target, timeout_seconds=max(timeout_seconds, 600)))
    return results


def results_to_json(results: list[ToolResult]) -> str:
    return json.dumps([r.to_dict() for r in results], indent=2)
