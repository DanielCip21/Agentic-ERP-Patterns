"""Pattern: CRM lead scoring agent using firmographics, engagement, and intent signals."""

from __future__ import annotations

from typing import Any
from datetime import datetime, timedelta
import random

from agentic_erp.agents.base import BaseERPAgent

# --- Simulated CRM backend ---

_LEADS: dict[str, dict] = {
    "LEAD-001": {
        "id": "LEAD-001",
        "name": "Alice Chen",
        "company": "TechCorp",
        "title": "VP Engineering",
        "company_size": 500,
        "industry": "Software",
        "score": None,
        "assigned_to": None,
    },
    "LEAD-002": {
        "id": "LEAD-002",
        "name": "Bob Martinez",
        "company": "RetailCo",
        "title": "Procurement Manager",
        "company_size": 50,
        "industry": "Retail",
        "score": None,
        "assigned_to": None,
    },
    "LEAD-003": {
        "id": "LEAD-003",
        "name": "Carol White",
        "company": "FinServ Ltd",
        "title": "CTO",
        "company_size": 2000,
        "industry": "Financial Services",
        "score": None,
        "assigned_to": None,
    },
}

_REPS: dict[str, dict] = {
    "REP-01": {
        "id": "REP-01",
        "name": "Sarah Kim",
        "capacity": 20,
        "current_leads": 12,
    },
    "REP-02": {"id": "REP-02", "name": "James Liu", "capacity": 20, "current_leads": 8},
}


def get_lead(lead_id: str) -> dict[str, Any]:
    lead = _LEADS.get(lead_id)
    return lead if lead else {"error": f"Lead {lead_id} not found"}


def get_engagement_history(lead_id: str) -> dict[str, Any]:
    if lead_id not in _LEADS:
        return {"error": f"Lead {lead_id} not found"}
    return {
        "lead_id": lead_id,
        "page_views": random.randint(2, 25),
        "email_opens": random.randint(0, 8),
        "demo_requested": random.choice([True, False]),
        "last_activity": (datetime.utcnow() - timedelta(days=random.randint(0, 14)))
        .date()
        .isoformat(),
        "content_downloaded": random.randint(0, 4),
    }


def score_lead(lead_id: str, score: int, reasoning: str) -> dict[str, Any]:
    if lead_id not in _LEADS:
        return {"error": f"Lead {lead_id} not found"}
    if not 0 <= score <= 100:
        return {"error": "Score must be between 0 and 100"}
    _LEADS[lead_id]["score"] = score
    _LEADS[lead_id]["reasoning"] = reasoning
    return {
        "lead_id": lead_id,
        "score": score,
        "tier": "hot" if score >= 70 else "warm" if score >= 40 else "cold",
    }


def assign_lead(lead_id: str, rep_id: str) -> dict[str, Any]:
    if lead_id not in _LEADS:
        return {"error": f"Lead {lead_id} not found"}
    if rep_id not in _REPS:
        return {"error": f"Rep {rep_id} not found"}
    _LEADS[lead_id]["assigned_to"] = rep_id
    _REPS[rep_id]["current_leads"] += 1
    return {
        "lead_id": lead_id,
        "assigned_to": rep_id,
        "rep_name": _REPS[rep_id]["name"],
    }


# --- Agent ---

_TOOLS = [
    {
        "name": "get_lead",
        "description": "Retrieve lead profile including company size, industry, and title.",
        "input_schema": {
            "type": "object",
            "properties": {"lead_id": {"type": "string"}},
            "required": ["lead_id"],
        },
    },
    {
        "name": "get_engagement_history",
        "description": "Get behavioral engagement signals: page views, email opens, demo requests.",
        "input_schema": {
            "type": "object",
            "properties": {"lead_id": {"type": "string"}},
            "required": ["lead_id"],
        },
    },
    {
        "name": "score_lead",
        "description": "Assign a 0–100 score and brief reasoning to a lead.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "string"},
                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                "reasoning": {"type": "string"},
            },
            "required": ["lead_id", "score", "reasoning"],
        },
    },
    {
        "name": "assign_lead",
        "description": "Assign a scored lead to a sales rep.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "string"},
                "rep_id": {"type": "string"},
            },
            "required": ["lead_id", "rep_id"],
        },
    },
]

_SYSTEM_PROMPT = """You are a CRM Lead Scoring Agent.
Score each lead 0–100 using firmographics (company size, industry, title seniority)
and engagement signals (page views, email opens, demo requests).
Hot leads (≥70) should be assigned to the most available sales rep.
Provide a one-sentence reasoning for each score."""


class LeadScoringAgent(BaseERPAgent):
    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_lead":
                return get_lead(**inputs)
            case "get_engagement_history":
                return get_engagement_history(**inputs)
            case "score_lead":
                return score_lead(**inputs)
            case "assign_lead":
                return assign_lead(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
