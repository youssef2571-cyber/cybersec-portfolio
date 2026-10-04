#!/usr/bin/env python3
"""
sentryx.cli
------------
Command-line entry point. Run with: python -m sentryx.cli
(or the installed `sentryx` console script - see pyproject.toml).
"""

from __future__ import annotations

import logging
import sys

import click
from rich.console import Console
from rich.table import Table

from .config import MissingConfigError, load_settings
from .db import Database
from .llm import AnalysisError, analyze_scan
from .report import render_html_report, render_pdf_report
from .tools import check_tool_availability, results_to_json, run_all
from .validators import InvalidTargetError, validate_target

console = Console()


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """SENTRY-X — AI-assisted authorized recon & vulnerability analysis."""
    ctx.ensure_object(dict)


@cli.command()
def check() -> None:
    """Check that required external binaries are installed."""
    availability = check_tool_availability()
    table = Table(title="Tool availability")
    table.add_column("Tool")
    table.add_column("Found on PATH")
    all_ok = True
    for name, ok in availability.items():
        table.add_row(name, "✅" if ok else "❌")
        all_ok = all_ok and ok
    console.print(table)
    if not all_ok:
        console.print("[red]Some tools are missing. See README for install instructions.[/red]")
        sys.exit(1)


@cli.command()
@click.option("--target", required=True, help="IP address, CIDR range, or hostname.")
@click.option("--authorized-by", default=None, help="Name of person who authorized this scan.")
@click.option(
    "--authorization-ref", default=None, help="Ticket/document reference for authorization."
)
@click.option("--include-nikto/--no-nikto", default=False, help="Include the (slow) nikto scan.")
@click.option("--timeout", default=120, help="Per-tool timeout in seconds.")
@click.option("--skip-ai", is_flag=True, help="Run recon only, skip AI analysis.")
def scan(
    target: str,
    authorized_by: str | None,
    authorization_ref: str | None,
    include_nikto: bool,
    timeout: int,
    skip_ai: bool,
) -> None:
    """Run a full recon scan against TARGET, store results, and (optionally)
    run AI analysis."""
    try:
        validate_target(target)
    except InvalidTargetError as exc:
        console.print(f"[red]Invalid target: {exc}[/red]")
        sys.exit(1)

    if not authorization_ref:
        console.print(
            "[yellow]Warning: no --authorization-ref provided. "
            "Proceeding anyway, but this scan's authorization will not be "
            "traceable in the report.[/yellow]"
        )
        if not click.confirm("Continue without an authorization reference?"):
            sys.exit(1)

    try:
        settings = load_settings(require_llm=not skip_ai, require_db=True)
    except MissingConfigError as exc:
        console.print(f"[red]{exc}[/red]")
        sys.exit(1)

    _setup_logging(settings.log_level)
    db = Database(settings)
    session_id = db.create_session(target, authorized_by, authorization_ref)
    console.print(f"[green]Created session #{session_id} for target {target}[/green]")

    try:
        with console.status("Running recon tools..."):
            results = run_all(target, include_nikto=include_nikto, timeout_seconds=timeout)

        for r in results:
            db.save_tool_run(
                session_id, r.tool, r.success, r.duration_seconds, r.raw_output, r.error
            )
            status = "[green]OK[/green]" if r.success else f"[red]FAILED ({r.error})[/red]"
            console.print(f"  {r.tool}: {status}")

        if skip_ai:
            db.set_session_status(session_id, "completed")
            console.print("[yellow]Skipped AI analysis (--skip-ai).[/yellow]")
            return

        with console.status("Running AI analysis..."):
            analysis = analyze_scan(
                api_key=settings.anthropic_api_key,
                model=settings.anthropic_model,
                target=target,
                tool_results=results,
                max_turns=settings.max_agentic_turns,
            )

        db.save_summary(
            session_id=session_id,
            raw_scan_json=results_to_json(results),
            ai_analysis=analysis.summary,
            risk_level=analysis.risk_level,
            model_used=settings.anthropic_model,
            input_tokens=analysis.input_tokens,
            output_tokens=analysis.output_tokens,
        )
        db.log_api_usage(
            session_id=session_id,
            model=settings.anthropic_model,
            input_tokens=analysis.input_tokens,
            output_tokens=analysis.output_tokens,
            estimated_cost_usd=None,
        )

        for finding in analysis.findings:
            vuln_id = db.save_vulnerability(
                session_id=session_id,
                vuln_name=finding.get("vuln_name", "Unnamed finding"),
                severity=finding.get("severity", "info"),
                port=finding.get("port"),
                service=finding.get("service"),
                description=finding.get("description"),
            )
            if finding.get("remediation"):
                db.save_fix(vuln_id, finding["remediation"])

        db.set_session_status(session_id, "completed")
        console.print(
            f"[green]Analysis complete. Risk level: {analysis.risk_level.upper()}[/green]"
        )
        console.print(f"Findings: {len(analysis.findings)}")

    except AnalysisError as exc:
        db.set_session_status(session_id, "failed")
        console.print(f"[red]AI analysis failed: {exc}[/red]")
        sys.exit(1)
    except Exception:
        db.set_session_status(session_id, "failed")
        raise
    finally:
        db.close()


@cli.command(name="list")
def list_sessions() -> None:
    """List past scan sessions."""
    settings = load_settings(require_llm=False, require_db=True)
    db = Database(settings)
    try:
        sessions = db.list_sessions()
        table = Table(title="Scan history")
        for col in ("ID", "Target", "Date", "Status", "Auth Ref"):
            table.add_column(col)
        for s in sessions:
            table.add_row(
                str(s["id"]),
                s["target"],
                str(s["scan_date"]),
                s["status"],
                s["authorization_ref"] or "—",
            )
        console.print(table)
    finally:
        db.close()


@cli.command()
@click.option("--session-id", required=True, type=int)
@click.option("--format", "fmt", type=click.Choice(["html", "pdf"]), default="html")
@click.option("--output", required=True, help="Output file path.")
def report(session_id: int, fmt: str, output: str) -> None:
    """Generate an HTML or PDF report for a past session."""
    settings = load_settings(require_llm=False, require_db=True)
    db = Database(settings)
    try:
        sess = db.get_session(session_id)
        if sess is None:
            console.print(f"[red]No session with id {session_id}[/red]")
            sys.exit(1)
        vulns = db.get_vulnerabilities(session_id)
        fixes_by_vuln = db.get_fixes_for_session(session_id)

        session_dict = {
            "target": sess.target,
            "scan_date": sess.scan_date,
            "authorization_ref": sess.authorization_ref,
        }

        if fmt == "html":
            html_content = render_html_report(session_dict, vulns, fixes_by_vuln, None)
            with open(output, "w", encoding="utf-8") as f:
                f.write(html_content)
        else:
            render_pdf_report(session_dict, vulns, fixes_by_vuln, None, output)

        console.print(f"[green]Report written to {output}[/green]")
    finally:
        db.close()


def main() -> None:
    cli(obj={})


if __name__ == "__main__":
    main()
