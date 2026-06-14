"""Simulated CRM tool implementations (swap for real CRM / Dataverse calls)."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any


_CONTACTS: dict[str, dict] = {
    "CON-001": {
        "id": "CON-001", "name": "Jane Smith", "email": "jane@contoso.com",
        "account_id": "ACC-001", "title": "VP Operations", "phone": "+1-555-0101",
    },
    "CON-002": {
        "id": "CON-002", "name": "Bob Johnson", "email": "bob@fabrikam.com",
        "account_id": "ACC-002", "title": "Procurement Manager", "phone": "+1-555-0202",
    },
    "CON-003": {
        "id": "CON-003", "name": "Sara Lee", "email": "sara@northwind.com",
        "account_id": "ACC-003", "title": "CEO", "phone": "+1-555-0303",
    },
}

_ACCOUNTS: dict[str, dict] = {
    "ACC-001": {
        "id": "ACC-001", "name": "Contoso Ltd", "industry": "Manufacturing",
        "arr": 48000, "health_score": 85, "tier": "Enterprise", "status": "active",
        "csm": "alice@erp.io",
    },
    "ACC-002": {
        "id": "ACC-002", "name": "Fabrikam Inc", "industry": "Retail",
        "arr": 22000, "health_score": 62, "tier": "Mid-Market", "status": "at-risk",
        "csm": "bob@erp.io",
    },
    "ACC-003": {
        "id": "ACC-003", "name": "Northwind Traders", "industry": "Distribution",
        "arr": 8500, "health_score": 91, "tier": "SMB", "status": "active",
        "csm": "alice@erp.io",
    },
}

_LEADS: dict[str, dict] = {
    "LEAD-001": {
        "id": "LEAD-001", "name": "Alice Brown", "company": "Adventure Works",
        "email": "alice@adventureworks.com", "score": 72, "status": "qualified",
        "source": "web", "assigned_to": "sales1@erp.io",
    },
    "LEAD-002": {
        "id": "LEAD-002", "name": "Charlie Davis", "company": "Tailspin Toys",
        "email": "charlie@tailspin.com", "score": 45, "status": "new",
        "source": "referral", "assigned_to": None,
    },
    "LEAD-003": {
        "id": "LEAD-003", "name": "Diana Prince", "company": "WingTip Curio",
        "email": "diana@wingtip.com", "score": 88, "status": "qualified",
        "source": "event", "assigned_to": "sales2@erp.io",
    },
}

_OPPORTUNITIES: dict[str, dict] = {
    "OPP-001": {
        "id": "OPP-001", "account_id": "ACC-001", "name": "Annual Renewal + Upsell",
        "value": 65000, "stage": "proposal", "probability": 75,
        "close_date": "2026-08-31", "owner": "sales1@erp.io",
    },
    "OPP-002": {
        "id": "OPP-002", "account_id": "ACC-002", "name": "New Module Implementation",
        "value": 28000, "stage": "discovery", "probability": 40,
        "close_date": "2026-09-15", "owner": "sales2@erp.io",
    },
}

_ACTIVITIES: list[dict] = []


def get_contact(contact_id: str) -> dict[str, Any]:
    c = _CONTACTS.get(contact_id)
    return c if c else {"error": f"Contact {contact_id} not found"}


def get_account(account_id: str) -> dict[str, Any]:
    a = _ACCOUNTS.get(account_id)
    return a if a else {"error": f"Account {account_id} not found"}


def list_at_risk_accounts() -> list[dict[str, Any]]:
    return [a for a in _ACCOUNTS.values() if a["health_score"] < 70]


def get_lead(lead_id: str) -> dict[str, Any]:
    l = _LEADS.get(lead_id)
    return l if l else {"error": f"Lead {lead_id} not found"}


def list_unassigned_leads() -> list[dict[str, Any]]:
    return [l for l in _LEADS.values() if l["assigned_to"] is None]


def qualify_lead(lead_id: str, score: int) -> dict[str, Any]:
    if lead_id not in _LEADS:
        return {"error": f"Lead {lead_id} not found"}
    _LEADS[lead_id]["score"] = score
    _LEADS[lead_id]["status"] = "qualified" if score >= 60 else "nurturing"
    return {**_LEADS[lead_id], "updated_at": datetime.utcnow().isoformat()}


def assign_lead(lead_id: str, sales_rep: str) -> dict[str, Any]:
    if lead_id not in _LEADS:
        return {"error": f"Lead {lead_id} not found"}
    _LEADS[lead_id]["assigned_to"] = sales_rep
    return {**_LEADS[lead_id], "assigned_at": datetime.utcnow().isoformat()}


def get_opportunity(opp_id: str) -> dict[str, Any]:
    o = _OPPORTUNITIES.get(opp_id)
    return o if o else {"error": f"Opportunity {opp_id} not found"}


def advance_opportunity_stage(opp_id: str, stage: str) -> dict[str, Any]:
    valid_stages = {"discovery", "qualification", "proposal", "negotiation", "closed-won", "closed-lost"}
    if stage not in valid_stages:
        return {"error": f"Invalid stage. Must be one of {valid_stages}"}
    if opp_id not in _OPPORTUNITIES:
        return {"error": f"Opportunity {opp_id} not found"}
    _OPPORTUNITIES[opp_id]["stage"] = stage
    return {**_OPPORTUNITIES[opp_id], "updated_at": datetime.utcnow().isoformat()}


def log_activity(entity_type: str, entity_id: str, activity_type: str, notes: str) -> dict[str, Any]:
    activity = {
        "id": f"ACT-{random.randint(1000, 9999)}",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "type": activity_type,
        "notes": notes,
        "logged_at": datetime.utcnow().isoformat(),
    }
    _ACTIVITIES.append(activity)
    return activity


def get_pipeline_summary() -> dict[str, Any]:
    total_value = sum(o["value"] for o in _OPPORTUNITIES.values())
    weighted = sum(o["value"] * o["probability"] / 100 for o in _OPPORTUNITIES.values())
    by_stage: dict[str, int] = {}
    for o in _OPPORTUNITIES.values():
        by_stage[o["stage"]] = by_stage.get(o["stage"], 0) + 1
    return {
        "total_pipeline_value": total_value,
        "weighted_pipeline": round(weighted, 2),
        "open_opportunities": len(_OPPORTUNITIES),
        "by_stage": by_stage,
    }
