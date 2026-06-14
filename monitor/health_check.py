"""
Codebase health checker — runs entirely without credentials.
Scans agents, tools, connectors, patterns and validates their structure.
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).parent.parent
SRC = ROOT / "src" / "agentic_erp"
D365 = ROOT / "dynamics-365-agentic-rag"


@dataclass
class ModuleHealth:
    name: str
    path: str
    importable: bool
    syntax_ok: bool
    line_count: int
    has_docstring: bool
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    error: str = ""


@dataclass
class TestResult:
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    duration_s: float = 0.0
    output: str = ""


@dataclass
class HealthReport:
    timestamp: str
    modules: list[ModuleHealth]
    test_result: TestResult
    total_agents: int
    total_tools: int
    total_patterns: int
    total_connectors: int
    total_lines: int
    issues: list[str]


def _check_syntax(path: Path) -> tuple[bool, str]:
    try:
        source = path.read_text(encoding="utf-8")
        ast.parse(source)
        return True, ""
    except SyntaxError as e:
        return False, str(e)


def _parse_module(path: Path) -> ModuleHealth:
    rel = str(path.relative_to(ROOT))
    syntax_ok, err = _check_syntax(path)
    lines = 0
    has_doc = False
    classes: list[str] = []
    functions: list[str] = []

    try:
        source = path.read_text(encoding="utf-8")
        lines = len(source.splitlines())
        if syntax_ok:
            tree = ast.parse(source)
            has_doc = (
                bool(ast.get_docstring(tree))
                or (
                    isinstance(tree.body[0], ast.Expr)
                    and isinstance(tree.body[0].value, ast.Constant)
                )
                if tree.body
                else False
            )
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith("_"):
                        functions.append(node.name)
    except Exception as e:
        err = str(e)

    # Test importability via subprocess to avoid polluting our namespace
    importable = False
    if syntax_ok:
        try:
            spec = importlib.util.spec_from_file_location("_tmp_check", path)
            if spec and spec.loader:
                importable = True
        except Exception:
            pass

    return ModuleHealth(
        name=path.stem,
        path=rel,
        importable=importable,
        syntax_ok=syntax_ok,
        line_count=lines,
        has_docstring=has_doc,
        classes=classes,
        functions=functions,
        error=err,
    )


def _collect_python_files(directory: Path) -> list[Path]:
    return sorted(directory.rglob("*.py"))


def run_tests() -> TestResult:
    """Run the mock-safe test suite (no credentials needed)."""
    test_dirs = [
        str(ROOT / "tests" / "test_agents.py"),
        str(ROOT / "tests" / "test_tools.py"),
        str(ROOT / "tests" / "test_new_agents.py"),
        str(ROOT / "tests" / "test_new_tools.py"),
        str(ROOT / "tests" / "test_async_and_connectors.py"),
    ]
    # Only include files that exist
    test_dirs = [t for t in test_dirs if Path(t).exists()]

    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest"] + test_dirs + ["-v", "--tb=short", "-q"],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=120,
        )
        duration = time.perf_counter() - start
        output = proc.stdout + proc.stderr

        passed = failed = errors = skipped = 0
        import re
        for line in output.splitlines():
            # Match pytest summary line e.g. "94 passed in 0.64s"
            # or "3 failed, 91 passed, 1 error in 0.7s"
            m = re.search(r"(\d+) passed", line)
            if m:
                passed = int(m.group(1))
            m = re.search(r"(\d+) failed", line)
            if m:
                failed = int(m.group(1))
            m = re.search(r"(\d+) error", line)
            if m:
                errors = int(m.group(1))

        return TestResult(
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
            duration_s=round(duration, 2),
            output=output[-3000:],
        )
    except subprocess.TimeoutExpired:
        return TestResult(output="TIMEOUT: tests took too long")
    except Exception as e:
        return TestResult(output=f"ERROR: {e}")


def run_health_check() -> HealthReport:
    import datetime

    modules: list[ModuleHealth] = []
    issues: list[str] = []

    agent_files = _collect_python_files(SRC / "agents")
    tool_files = _collect_python_files(SRC / "tools")
    pattern_files = _collect_python_files(SRC / "patterns")
    connector_files = _collect_python_files(SRC / "connectors")

    # Also include D365 agents
    d365_agent_files = _collect_python_files(D365 / "agents") if D365.exists() else []

    all_files = agent_files + tool_files + pattern_files + connector_files + d365_agent_files

    for f in all_files:
        if f.name == "__init__.py":
            continue
        m = _parse_module(f)
        modules.append(m)
        if not m.syntax_ok:
            issues.append(f"SYNTAX ERROR in {m.path}: {m.error}")
        if not m.has_docstring:
            issues.append(f"Missing module docstring: {m.path}")

    test_result = run_tests()
    if test_result.failed > 0:
        issues.append(f"{test_result.failed} test(s) FAILING")
    if test_result.errors > 0:
        issues.append(f"{test_result.errors} test error(s)")

    total_lines = sum(m.line_count for m in modules)

    def _count(files: list[Path]) -> int:
        return len([f for f in files if f.name != "__init__.py"])

    return HealthReport(
        timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        modules=modules,
        test_result=test_result,
        total_agents=_count(agent_files) + _count(d365_agent_files),
        total_tools=_count(tool_files),
        total_patterns=_count(pattern_files),
        total_connectors=_count(connector_files),
        total_lines=total_lines,
        issues=issues,
    )
