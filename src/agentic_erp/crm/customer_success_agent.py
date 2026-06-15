"""Pattern: CRM customer success agent monitoring health scores and triggering interventions."""

from __future__ import annotations

from typing import Any
from datetime import datetime

from agentic_erp.agents.base import BaseERPAgent

# --- Simulated backend ---

_ACCOUNTS: dict[str, dict] = {
    "ACC-001": {
        "id": "ACC-001",
        "name": "Contoso Ltd",
        "arr": 48000,
        "health_score": 82,
        "nps": 8,
        "last_login_days_ago": 2,
        "open_tickets": 1,
        "csm": "CSM-01",
    },
    "ACC-002": {
        "id": "ACC-002",
        "name": "Fabrikam Inc",
        "arr": 120000,
        "health_score": 41,
        "nps": 4,
        "last_login_days_ago": 18,
        "open_tickets": 5,
        "csm": "CSM-02",
    },
    "ACC-003": {
        "id": "ACC-003",
        "name": "Woodgrove Bank",
        "arr": 220000,
        "health_score": 27,
        "nps": 2,
        "last_login_days_ago": 30,
        "open_tickets": 12,
        "csm": "CSM-01",
    },
}

_SUCCESS_PLANS: list[dict] = []
_INTERACTIONS: list[dict] = []


def get_account_health(account_id: str) -> dict[str, Any]:
    acct = _ACCOUNTS.get(account_id)
    return acct if acct else {"error": f"Account {account_id} not found"}


def list_at_risk_accounts(threshold: int = 60) -> list[dict[str, Any]]:
    return [a for a in _ACCOUNTS.values() if a["health_score"] < threshold]


def create_success_plan(account_id: str, actions: list[str]) -> dict[str, Any]:
    if account_id not in _ACCOUNTS:
        return {"error": f"Account {account_id} not found"}
    plan = {
        "plan_id": f"SP-{len(_SUCCESS_PLANS) + 1:03d}",
        "account_id": account_id,
        "actions": actions,
        "created_at": datetime.utcnow().isoformat(),
        "status": "active",
    }
    _SUCCESS_PLANS.append(plan)
    return plan


def log_customer_interaction(account_id: str, notes: str) -> dict[str, Any]:
    if account_id not in _ACCOUNTS:
        return {"error": f"Account {account_id} not found"}
    interaction = {
        "id": f"INT-{len(_INTERACTIONS) + 1:03d}",
        "account_id": account_id,
        "notes": notes,
        "logged_at": datetime.utcnow().isoformat(),
    }
    _INTERACTIONS.append(interaction)
    return interaction


# --- Agent ---

_TOOLS = [
    {
        "name": "get_account_health",
        "description": "Get health score, NPS, login recency, and open ticket count for an account.",
        "input_schema": {
            "type": "object",
            "properties": {"account_id": {"type": "string"}},
            "required": ["account_id"],
        },
    },
    {
        "name": "list_at_risk_accounts",
        "description": "List all accounts with health score below a threshold (default 60).",
        "input_schema": {
            "type": "object",
            "properties": {"threshold": {"type": "integer", "default": 60}},
        },
    },
    {
        "name": "create_success_plan",
        "description": "Create a success plan with a list of intervention actions for an account.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "actions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["account_id", "actions"],
        },
    },
    {
        "name": "log_customer_interaction",
        "description": "Log a CSM interaction or call note for an account.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["account_id", "notes"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Customer Success Agent for an enterprise SaaS company.
Identify at-risk accounts (health score <60), analyse why they are at risk using health metrics,
and create targeted success plans with specific actions (e.g. executive business review,
feature training, ticket escalation). Always log a summary interaction note."""


class CustomerSuccessAgent(BaseERPAgent):
    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_account_health":
                return get_account_health(**inputs)
            case "list_at_risk_accounts":
                return list_at_risk_accounts(**inputs)
            case "create_success_plan":
                return create_success_plan(**inputs)
            case "log_customer_interaction":
                return log_customer_interaction(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
