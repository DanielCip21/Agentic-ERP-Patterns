"""
Daily report generator — saves a dated JSON + Markdown report to monitor/reports/.
Run once per day (cron, CI, or manually).

Usage:
    python monitor/daily_report.py
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from monitor.health_check import HealthReport, run_health_check  # noqa: E402

REPORTS_DIR = ROOT / "monitor" / "reports"


def _markdown(report: HealthReport, date: str) -> str:
    t = report.test_result
    all_green = t.failed == 0 and t.errors == 0
    status_badge = "PASS" if all_green else "FAIL"

    lines = [
        f"# Daily Health Report — {date}",
        "",
        f"**Status:** `{status_badge}`  |  **Generated:** {report.timestamp}",
        "",
        "## Platform Metrics",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Agents | {report.total_agents} |",
        f"| Tools | {report.total_tools} |",
        f"| Orchestration Patterns | {report.total_patterns} |",
        f"| Infrastructure Connectors | {report.total_connectors} |",
        f"| Total Source Lines | {report.total_lines} |",
        "",
        "## Test Suite (mock mode)",
        "",
        f"| Result | Count |",
        f"|--------|-------|",
        f"| Passed | {t.passed} |",
        f"| Failed | {t.failed} |",
        f"| Errors | {t.errors} |",
        f"| Duration | {t.duration_s}s |",
        "",
        "## Module Status",
        "",
        "| Module | Path | Lines | Syntax | Docstring |",
        "|--------|------|-------|--------|-----------|",
    ]
    for m in report.modules:
        lines.append(
            f"| {m.name} | `{m.path}` | {m.line_count} "
            f"| {'✓' if m.syntax_ok else '✗'} "
            f"| {'✓' if m.has_docstring else '✗'} |"
        )

    lines += ["", "## Issues", ""]
    if report.issues:
        for issue in report.issues:
            lines.append(f"- ⚠️ {issue}")
    else:
        lines.append("_No issues found. All checks passed._")

    lines += [
        "",
        "---",
        "_This report was generated automatically by the Agentic ERP demo monitoring system._",
        "_Mode: DEMO / TEST / CONCEPT — no live credentials required._",
    ]
    return "\n".join(lines)


def generate() -> dict:
    """Run health check and write report files. Returns summary dict."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    report = run_health_check()
    date = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    md_path = REPORTS_DIR / f"report_{date}.md"
    json_path = REPORTS_DIR / f"report_{date}.json"

    # Write Markdown
    md_path.write_text(_markdown(report, date), encoding="utf-8")

    # Write JSON
    json_data = {
        "date": date,
        "timestamp": report.timestamp,
        "status": "PASS" if report.test_result.failed == 0 and report.test_result.errors == 0 else "FAIL",
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
        "issues": report.issues,
    }
    json_path.write_text(json.dumps(json_data, indent=2), encoding="utf-8")

    print(f"Reports written:")
    print(f"  {md_path}")
    print(f"  {json_path}")
    print(f"Status: {json_data['status']}")
    print(f"Tests:  {report.test_result.passed} passed, {report.test_result.failed} failed")
    if report.issues:
        print(f"Issues ({len(report.issues)}):")
        for i in report.issues:
            print(f"  → {i}")
    else:
        print("Issues: none")

    return json_data


if __name__ == "__main__":
    result = generate()
    sys.exit(0 if result["status"] == "PASS" else 1)
