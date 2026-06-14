"""CRM Agent — manages leads, contacts, accounts, and opportunities."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import crm_tools

_TOOLS = [
    {
        "name": "get_contact",
        "description": "Retrieve contact details by contact ID.",
        "input_schema": {
            "type": "object",
            "properties": {"contact_id": {"type": "string"}},
            "required": ["contact_id"],
        },
    },
    {
        "name": "get_account",
        "description": "Retrieve account details including health score, ARR, and tier.",
        "input_schema": {
            "type": "object",
            "properties": {"account_id": {"type": "string"}},
            "required": ["account_id"],
        },
    },
    {
        "name": "list_at_risk_accounts",
        "description": "List all accounts with a health score below 70 (at-risk of churn).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_lead",
        "description": "Retrieve lead details by lead ID.",
        "input_schema": {
            "type": "object",
            "properties": {"lead_id": {"type": "string"}},
            "required": ["lead_id"],
        },
    },
    {
        "name": "list_unassigned_leads",
        "description": "List all leads that have not yet been assigned to a sales rep.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "qualify_lead",
        "description": "Score and qualify a lead. Score >= 60 marks it as qualified, otherwise nurturing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "string"},
                "score": {"type": "integer", "minimum": 0, "maximum": 100},
            },
            "required": ["lead_id", "score"],
        },
    },
    {
        "name": "assign_lead",
        "description": "Assign a lead to a sales representative by email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "string"},
                "sales_rep": {"type": "string", "description": "Email of the sales rep"},
            },
            "required": ["lead_id", "sales_rep"],
        },
    },
    {
        "name": "get_opportunity",
        "description": "Retrieve opportunity details by opportunity ID.",
        "input_schema": {
            "type": "object",
            "properties": {"opp_id": {"type": "string"}},
            "required": ["opp_id"],
        },
    },
    {
        "name": "advance_opportunity_stage",
        "description": "Move an opportunity to the next stage in the sales pipeline.",
        "input_schema": {
            "type": "object",
            "properties": {
                "opp_id": {"type": "string"},
                "stage": {
                    "type": "string",
                    "enum": ["discovery", "qualification", "proposal", "negotiation", "closed-won", "closed-lost"],
                },
            },
            "required": ["opp_id", "stage"],
        },
    },
    {
        "name": "log_activity",
        "description": "Log a CRM activity (call, email, meeting) against a contact, account, lead, or opportunity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_type": {"type": "string", "enum": ["contact", "account", "lead", "opportunity"]},
                "entity_id": {"type": "string"},
                "activity_type": {"type": "string", "enum": ["call", "email", "meeting", "note"]},
                "notes": {"type": "string"},
            },
            "required": ["entity_type", "entity_id", "activity_type", "notes"],
        },
    },
    {
        "name": "get_pipeline_summary",
        "description": "Get a summary of the entire sales pipeline: total value, weighted forecast, and breakdown by stage.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

_SYSTEM_PROMPT = """You are a CRM Agent for a B2B software company.
Your responsibilities:
- Manage leads: score, qualify, and assign them to sales reps
- Monitor account health and flag accounts at risk of churn
- Track opportunities through the sales pipeline
- Log customer interactions (calls, emails, meetings)
- Provide pipeline summaries and forecasts

Always prioritize at-risk accounts and high-score unassigned leads.
Be data-driven, concise, and action-oriented in your responses."""


class CRMAgent(BaseERPAgent):
    """Manages CRM operations: leads, contacts, accounts, and opportunities."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_contact":
                return crm_tools.get_contact(**inputs)
            case "get_account":
                return crm_tools.get_account(**inputs)
            case "list_at_risk_accounts":
                return crm_tools.list_at_risk_accounts()
            case "get_lead":
                return crm_tools.get_lead(**inputs)
            case "list_unassigned_leads":
                return crm_tools.list_unassigned_leads()
            case "qualify_lead":
                return crm_tools.qualify_lead(**inputs)
            case "assign_lead":
                return crm_tools.assign_lead(**inputs)
            case "get_opportunity":
                return crm_tools.get_opportunity(**inputs)
            case "advance_opportunity_stage":
                return crm_tools.advance_opportunity_stage(**inputs)
            case "log_activity":
                return crm_tools.log_activity(**inputs)
            case "get_pipeline_summary":
                return crm_tools.get_pipeline_summary()
            case _:
                return {"error": f"Unknown tool: {name}"}
