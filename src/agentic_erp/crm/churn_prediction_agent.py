"""Pattern: CRM churn prediction agent — risk scores, signal analysis, retention playbooks."""

from __future__ import annotations

from typing import Any
from datetime import datetime

from agentic_erp.agents.base import BaseERPAgent

# ---------------------------------------------------------------------------
# Simulated backend data
# ---------------------------------------------------------------------------
_CHURN_RISK: dict[str, dict] = {
    "ACC-001": {"account_id": "ACC-001", "name": "Contoso Ltd", "churn_risk_score": 0.12, "arr": 48000},
    "ACC-002": {"account_id": "ACC-002", "name": "Fabrikam Inc", "churn_risk_score": 0.68, "arr": 120000},
    "ACC-003": {"account_id": "ACC-003", "name": "Woodgrove Bank", "churn_risk_score": 0.85, "arr": 220000},
    "ACC-004": {"account_id": "ACC-004", "name": "Tailspin Toys", "churn_risk_score": 0.31, "arr": 35000},
}

_CHURN_SIGNALS: dict[str, list[str]] = {
    "ACC-001": ["Consistent usage", "Recent NPS upgrade"],
    "ACC-002": ["Login frequency dropped 40% in 30d", "3 unresolved support tickets", "NPS declined from 7 to 4"],
    "ACC-003": ["No logins in 30 days", "Contract renewal due in 45 days", "Champion left company", "12 open tickets"],
    "ACC-004": ["Slight usage dip", "New champion onboarded recently"],
}

_PLAYBOOKS: dict[str, list[str]] = {
    "executive_outreach": ["Schedule EBR with C-suite", "Share product roadmap", "Offer executive sponsorship"],
    "feature_adoption": ["Assign dedicated CSM training sessions", "Enable premium feature access", "Share success stories"],
    "support_escalation": ["Prioritise open ticket resolution", "Assign dedicated support engineer", "Daily status updates"],
    "renewal_risk": ["Prepare renewal proposal early", "Offer multi-year discount", "Executive sponsor call"],
}

_RETENTION_ACTIONS: list[dict] = []


def _get_churn_risk_scores() -> list[dict[str, Any]]:
    return sorted(_CHURN_RISK.values(), key=lambda x: x["churn_risk_score"], reverse=True)


def _analyze_churn_signals(account_id: str) -> dict[str, Any]:
    risk = _CHURN_RISK.get(account_id)
    if not risk:
        return {"error": f"Account {account_id} not found"}
    signals = _CHURN_SIGNALS.get(account_id, [])
    risk_level = "high" if risk["churn_risk_score"] >= 0.7 else "medium" if risk["churn_risk_score"] >= 0.4 else "low"
    return {
        "account_id": account_id,
        "account_name": risk["name"],
        "churn_risk_score": risk["churn_risk_score"],
        "risk_level": risk_level,
        "signals": signals,
        "analyzed_at": datetime.utcnow().isoformat(),
    }


def _trigger_retention_playbook(account_id: str, playbook_type: str) -> dict[str, Any]:
    if account_id not in _CHURN_RISK:
        return {"error": f"Account {account_id} not found"}
    if playbook_type not in _PLAYBOOKS:
        return {"error": f"Playbook '{playbook_type}' not found. Available: {list(_PLAYBOOKS.keys())}"}
    return {
        "account_id": account_id,
        "playbook_type": playbook_type,
        "actions": _PLAYBOOKS[playbook_type],
        "triggered_at": datetime.utcnow().isoformat(),
        "status": "active",
    }


def _log_retention_action(account_id: str, action: str) -> dict[str, Any]:
    if account_id not in _CHURN_RISK:
        return {"error": f"Account {account_id} not found"}
    entry = {
        "id": f"RA-{len(_RETENTION_ACTIONS) + 1:04d}",
        "account_id": account_id,
        "action": action,
        "logged_at": datetime.utcnow().isoformat(),
    }
    _RETENTION_ACTIONS.append(entry)
    return entry


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
_TOOLS = [
    {
        "name": "get_churn_risk_scores",
        "description": "Retrieve churn risk scores for all accounts, sorted by risk descending.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "analyze_churn_signals",
        "description": "Analyse the specific churn signals contributing to an account's risk score.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "Account ID to analyse"},
            },
            "required": ["account_id"],
        },
    },
    {
        "name": "trigger_retention_playbook",
        "description": "Trigger a retention playbook for an at-risk account. Available types: executive_outreach, feature_adoption, support_escalation, renewal_risk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "Account ID"},
                "playbook_type": {"type": "string", "description": "Playbook type to trigger"},
            },
            "required": ["account_id", "playbook_type"],
        },
    },
    {
        "name": "log_retention_action",
        "description": "Log a specific retention action taken for an account.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "Account ID"},
                "action": {"type": "string", "description": "Description of the action taken"},
            },
            "required": ["account_id", "action"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Churn Prediction and Retention Agent for a SaaS platform.
Your responsibilities:
1. Identify accounts at high churn risk (score >= 0.7)
2. Analyse specific churn signals for each at-risk account
3. Trigger appropriate retention playbooks based on the signal pattern
4. Log all retention actions taken for audit and follow-up

Prioritise high-ARR accounts at high churn risk. Always analyse signals before triggering a playbook.
Escalate accounts with multiple critical signals to the VP of Customer Success."""


class ChurnPredictionAgent(BaseERPAgent):
    """Predicts churn risk and triggers targeted retention interventions."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_churn_risk_scores":
                return _get_churn_risk_scores()
            case "analyze_churn_signals":
                return _analyze_churn_signals(**inputs)
            case "trigger_retention_playbook":
                return _trigger_retention_playbook(**inputs)
            case "log_retention_action":
                return _log_retention_action(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
