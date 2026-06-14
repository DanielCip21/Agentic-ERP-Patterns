"""
Demo Monitoring Dashboard — Agentic ERP+CRM Platform
Runs fully offline / without credentials. Test/concept mode.

Usage:
    python monitor/demo_monitor.py            # single snapshot
    python monitor/demo_monitor.py --watch    # live refresh every 60s
    python monitor/demo_monitor.py --json     # machine-readable output
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from monitor.health_check import HealthReport, run_health_check  # noqa: E402


# ── ANSI colours (disabled if not a tty) ──────────────────────────────────────
_USE_COLOUR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if not _USE_COLOUR:
        return text
    return f"\033[{code}m{text}\033[0m"


GREEN  = lambda t: _c("32", t)   # noqa: E731
YELLOW = lambda t: _c("33", t)   # noqa: E731
RED    = lambda t: _c("31", t)   # noqa: E731
CYAN   = lambda t: _c("36", t)   # noqa: E731
BOLD   = lambda t: _c("1",  t)   # noqa: E731
DIM    = lambda t: _c("2",  t)   # noqa: E731


# ── Rendering ─────────────────────────────────────────────────────────────────

def _status_icon(ok: bool) -> str:
    return GREEN("✓") if ok else RED("✗")


def _render(report: HealthReport) -> str:
    lines: list[str] = []

    def ln(s: str = "") -> None:
        lines.append(s)

    ln(BOLD("╔══════════════════════════════════════════════════════════════╗"))
    ln(BOLD("║       AGENTIC ERP+CRM  —  MONITORING DASHBOARD              ║"))
    ln(BOLD("║       MODE: DEMO / TEST / CONCEPT  (no credentials)         ║"))
    ln(BOLD("╚══════════════════════════════════════════════════════════════╝"))
    ln(DIM(f"  Last checked: {report.timestamp}"))
    ln()

    # ── Platform metrics ──────────────────────────────────────────────────────
    ln(BOLD("  PLATFORM METRICS"))
    ln(f"  {'Agents':<20} {CYAN(str(report.total_agents))}")
    ln(f"  {'Tools':<20} {CYAN(str(report.total_tools))}")
    ln(f"  {'Orchestration Patterns':<20} {CYAN(str(report.total_patterns))}")
    ln(f"  {'Infrastructure Connectors':<20} {CYAN(str(report.total_connectors))}")
    ln(f"  {'Total Source Lines':<20} {CYAN(str(report.total_lines))}")
    ln()

    # ── Test suite ────────────────────────────────────────────────────────────
    t = report.test_result
    total_tests = t.passed + t.failed + t.errors
    all_passed = t.failed == 0 and t.errors == 0
    ln(BOLD("  TEST SUITE  (mock mode — no live API calls)"))
    ln(f"  {_status_icon(all_passed)}  {GREEN(str(t.passed)) if t.passed else '0'} passed  "
       f"{'/ ' + RED(str(t.failed) + ' failed') if t.failed else ''}  "
       f"{'/ ' + RED(str(t.errors) + ' errors') if t.errors else ''}  "
       f"in {t.duration_s}s")
    ln()

    # ── Module status ─────────────────────────────────────────────────────────
    ln(BOLD("  MODULE STATUS"))
    agents   = [m for m in report.modules if "agent" in m.path]
    tools    = [m for m in report.modules if "tool"  in m.path]
    patterns = [m for m in report.modules if "pattern" in m.path]
    connectors = [m for m in report.modules if "connector" in m.path]

    for group_name, group in [
        ("Agents",      agents),
        ("Tools",       tools),
        ("Patterns",    patterns),
        ("Connectors",  connectors),
    ]:
        if not group:
            continue
        ln(f"  {DIM(group_name + ':')}")
        for m in group:
            icon = _status_icon(m.syntax_ok)
            doc_note = "" if m.has_docstring else DIM("  [no docstring]")
            ln(f"    {icon} {m.name:<35} {DIM(str(m.line_count) + 'L')}{doc_note}")
        ln()

    # ── Issues ────────────────────────────────────────────────────────────────
    if report.issues:
        ln(BOLD("  ISSUES FOUND"))
        for issue in report.issues:
            ln(f"  {RED('→')} {issue}")
        ln()
    else:
        ln(f"  {GREEN('✓')} {GREEN('No issues found — all checks passed.')}")
        ln()

    # ── Legend ────────────────────────────────────────────────────────────────
    ln(DIM("  ─────────────────────────────────────────────────────────────"))
    ln(DIM("  CONCEPT MODE: Connectors show structure only."))
    ln(DIM("  Add credentials to .env to enable live agent runs."))
    ln(DIM("  Run with --watch to refresh every 60 seconds."))

    return "\n".join(lines)


def _to_json(report: HealthReport) -> str:
    return json.dumps(
        {
            "timestamp": report.timestamp,
            "metrics": {
                "agents": report.total_agents,
                "tools": report.total_tools,
                "patterns": report.total_patterns,
                "connectors": report.total_connectors,
                "source_lines": report.total_lines,
            },
            "tests": {
                "passed": report.test_result.passed,
                "failed": report.test_result.failed,
                "errors": report.test_result.errors,
                "duration_s": report.test_result.duration_s,
            },
            "modules": [
                {
                    "name": m.name,
                    "path": m.path,
                    "syntax_ok": m.syntax_ok,
                    "has_docstring": m.has_docstring,
                    "line_count": m.line_count,
                    "classes": m.classes,
                    "functions": m.functions,
                    "error": m.error,
                }
                for m in report.modules
            ],
            "issues": report.issues,
        },
        indent=2,
    )


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic ERP Demo Monitor")
    parser.add_argument("--watch",    action="store_true", help="Refresh every 60 seconds")
    parser.add_argument("--interval", type=int, default=60, help="Refresh interval in seconds")
    parser.add_argument("--json",     action="store_true", help="Output JSON")
    args = parser.parse_args()

    def run_once() -> None:
        report = run_health_check()
        if args.json:
            print(_to_json(report))
        else:
            if sys.stdout.isatty():
                # Clear screen for watch mode
                print("\033[2J\033[H", end="")
            print(_render(report))

    if args.watch:
        print(f"Monitoring Agentic ERP — refreshing every {args.interval}s  (Ctrl+C to stop)")
        while True:
            try:
                run_once()
                time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\nMonitor stopped.")
                break
    else:
        run_once()


if __name__ == "__main__":
    main()
