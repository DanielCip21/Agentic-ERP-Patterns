"""Autonomous Profitability Agent.

Combines all ten specialist engineering personas into a single agentic loop
that continuously evaluates and improves every ERP operation through a
profitability lens.
"""

from __future__ import annotations

import json
from typing import Any

import anthropic

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.prompts.autonomous_prompts import (
    AUTONOMOUS_PROFITABILITY_SYSTEM,
    get_persona_prompt,
)

# ── Tool schemas (Claude tool-use format) ───────────────────────────────────

TOOLS: list[dict] = [
    {
        "name": "analyze_profitability",
        "description": (
            "Analyse current ERP metrics and return a ranked list of profit "
            "levers with estimated financial impact."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "focus_area": {
                    "type": "string",
                    "enum": [
                        "revenue",
                        "cost_reduction",
                        "cash_flow",
                        "margin",
                        "overall",
                    ],
                    "description": "Which profit dimension to prioritise.",
                },
                "time_horizon_days": {
                    "type": "integer",
                    "description": "Look-back window for trend data (default 30).",
                },
            },
            "required": ["focus_area"],
        },
    },
    {
        "name": "audit_codebase_quality",
        "description": (
            "Run a senior-engineer audit of the codebase and return a "
            "prioritised list of quality / architecture issues."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "persona": {
                    "type": "string",
                    "enum": [
                        "codebase_auditor",
                        "architecture_rebuilder",
                        "technical_lead",
                    ],
                    "description": "Specialist lens to apply during the audit.",
                },
                "module": {
                    "type": "string",
                    "description": "Specific module or file path to inspect (optional).",
                },
            },
            "required": ["persona"],
        },
    },
    {
        "name": "optimize_performance",
        "description": (
            "Profile performance hot-spots and return optimisation strategies "
            "ranked by expected throughput gain."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Component or query to profile.",
                },
                "metric": {
                    "type": "string",
                    "enum": ["latency", "memory", "cpu", "database_queries", "all"],
                    "description": "Performance metric to focus on.",
                },
            },
            "required": ["target", "metric"],
        },
    },
    {
        "name": "run_security_audit",
        "description": (
            "Perform a production security audit and return a severity-ranked "
            "vulnerability report with secure-fix recommendations."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["api", "auth", "data", "infrastructure", "full"],
                    "description": "Audit scope.",
                },
            },
            "required": ["scope"],
        },
    },
    {
        "name": "assess_devops_readiness",
        "description": (
            "Evaluate CI/CD pipeline, monitoring coverage, and deployment "
            "reliability; return an actionable production-readiness checklist."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "environment": {
                    "type": "string",
                    "enum": ["staging", "production", "both"],
                    "description": "Target environment to assess.",
                },
            },
            "required": ["environment"],
        },
    },
    {
        "name": "generate_profitability_report",
        "description": (
            "Synthesise findings from all specialist analyses into an "
            "executive-ready profitability report with a ranked action plan."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "include_sections": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Sections to include: revenue_levers, cost_savings, "
                        "security_risks, performance_gains, architecture_debt, "
                        "devops_gaps."
                    ),
                },
                "format": {
                    "type": "string",
                    "enum": ["markdown", "json", "executive_summary"],
                    "description": "Output format.",
                },
            },
            "required": ["include_sections", "format"],
        },
    },
]


# ── Stub implementations (swap for real Dataverse / telemetry calls) ─────────

def _analyze_profitability(focus_area: str, time_horizon_days: int = 30) -> dict:
    return {
        "focus_area": focus_area,
        "time_horizon_days": time_horizon_days,
        "top_levers": [
            {
                "rank": 1,
                "lever": "Reduce overdue receivables",
                "estimated_impact_usd": 142_000,
                "effort": "low",
                "persona": "performance_optimizer",
            },
            {
                "rank": 2,
                "lever": "Eliminate redundant API calls in inventory sync",
                "estimated_impact_usd": 28_000,
                "effort": "medium",
                "persona": "codebase_auditor",
            },
            {
                "rank": 3,
                "lever": "Automate PO approval via AI routing",
                "estimated_impact_usd": 55_000,
                "effort": "medium",
                "persona": "startup_engineer",
            },
        ],
        "total_addressable_value_usd": 225_000,
    }


def _audit_codebase_quality(persona: str, module: str | None = None) -> dict:
    prompt_snippet = get_persona_prompt(persona)[:120] + "..."
    return {
        "persona_applied": persona,
        "module": module or "full codebase",
        "persona_directive": prompt_snippet,
        "findings": [
            {
                "severity": "high",
                "issue": "Tight coupling between order and inventory modules",
                "recommendation": "Extract shared domain events via a message bus",
            },
            {
                "severity": "medium",
                "issue": "Duplicated validation logic across three agents",
                "recommendation": "Centralise in a shared validators module",
            },
            {
                "severity": "low",
                "issue": "Missing type hints on _dispatch_tool overrides",
                "recommendation": "Add return type annotations for mypy compliance",
            },
        ],
    }


def _optimize_performance(target: str, metric: str) -> dict:
    return {
        "target": target,
        "metric": metric,
        "bottlenecks": [
            {
                "rank": 1,
                "description": "N+1 query pattern in inventory list endpoint",
                "gain_percent": 65,
                "fix": "Add select_related / batch fetch",
            },
            {
                "rank": 2,
                "description": "Synchronous D365 calls blocking the agentic loop",
                "gain_percent": 40,
                "fix": "Switch to AsyncBaseERPAgent with asyncio.gather",
            },
        ],
    }


def _run_security_audit(scope: str) -> dict:
    return {
        "scope": scope,
        "vulnerabilities": [
            {
                "severity": "critical",
                "category": "Sensitive data exposure",
                "detail": "D365_CLIENT_SECRET logged at DEBUG level",
                "fix": "Mask secrets before logging; use structured log redaction",
            },
            {
                "severity": "high",
                "category": "Authentication flaw",
                "detail": "Token refresh not retried on 401 in d365 connector",
                "fix": "Implement exponential-backoff retry with token refresh",
            },
            {
                "severity": "medium",
                "category": "API weakness",
                "detail": "No rate-limit handling on outbound Dataverse calls",
                "fix": "Add Retry-After header inspection and back-off",
            },
        ],
    }


def _assess_devops_readiness(environment: str) -> dict:
    return {
        "environment": environment,
        "readiness_score": 62,
        "checklist": [
            {"item": "CI pipeline runs unit tests on every PR", "status": "pass"},
            {"item": "Coverage gate ≥ 80 %", "status": "fail", "current": "71 %"},
            {"item": "Docker image built and scanned", "status": "missing"},
            {"item": "Health-check endpoint exposed", "status": "missing"},
            {"item": "Structured JSON logging", "status": "pass"},
            {"item": "Secret rotation policy documented", "status": "fail"},
            {"item": "Rollback procedure tested", "status": "missing"},
        ],
    }


def _generate_profitability_report(
    include_sections: list[str], fmt: str
) -> dict:
    report = {
        "title": "Autonomous Profitability Report",
        "format": fmt,
        "sections": include_sections,
        "executive_summary": (
            "Three high-ROI actions can unlock ~$225k in annualised value: "
            "(1) fix overdue receivables workflow, "
            "(2) eliminate inventory sync API waste, "
            "(3) automate PO approvals with AI routing. "
            "Additionally, one critical security gap (secret logging) requires "
            "immediate remediation to protect revenue continuity."
        ),
        "action_plan": [
            {
                "priority": 1,
                "action": "Patch secret logging — 1 dev-hour",
                "impact": "Risk mitigation / compliance",
            },
            {
                "priority": 2,
                "action": "Fix N+1 query in inventory — 4 dev-hours",
                "impact": "$28k cost saving + 65% latency reduction",
            },
            {
                "priority": 3,
                "action": "Automate PO approval agent — 2 dev-days",
                "impact": "$55k saving",
            },
            {
                "priority": 4,
                "action": "Receivables follow-up agent — 3 dev-days",
                "impact": "$142k cash-flow improvement",
            },
        ],
    }
    return report


# ── Agent ────────────────────────────────────────────────────────────────────

class AutonomousProfitabilityAgent(BaseERPAgent):
    """Autonomous agent that applies all ten specialist personas to ensure
    every ERP operation maximises profitability.

    Defaults to claude-sonnet-4-6 for the reasoning depth required by
    multi-persona synthesis.
    """

    DEFAULT_MODEL = "claude-sonnet-4-6"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        client: anthropic.Anthropic | None = None,
    ) -> None:
        super().__init__(
            tools=TOOLS,
            system_prompt=AUTONOMOUS_PROFITABILITY_SYSTEM,
            model=model,
            client=client,
        )

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        if name == "analyze_profitability":
            return _analyze_profitability(
                inputs["focus_area"],
                inputs.get("time_horizon_days", 30),
            )
        if name == "audit_codebase_quality":
            return _audit_codebase_quality(
                inputs["persona"],
                inputs.get("module"),
            )
        if name == "optimize_performance":
            return _optimize_performance(inputs["target"], inputs["metric"])
        if name == "run_security_audit":
            return _run_security_audit(inputs["scope"])
        if name == "assess_devops_readiness":
            return _assess_devops_readiness(inputs["environment"])
        if name == "generate_profitability_report":
            return _generate_profitability_report(
                inputs["include_sections"],
                inputs.get("format", "markdown"),
            )
        raise NotImplementedError(f"Unknown tool: {name}")
