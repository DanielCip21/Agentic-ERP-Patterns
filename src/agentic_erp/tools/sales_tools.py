"""Simulated Sales & Project Management tools."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any


_OPPORTUNITIES: dict[str, dict] = {
    "OPP-001": {"id": "OPP-001", "customer": "Contoso Ltd", "value": 280000.00, "stage": "negotiation", "close_date": "2025-03-31", "probability": 0.75},
    "OPP-002": {"id": "OPP-002", "customer": "Fabrikam Inc", "value": 95000.00, "stage": "proposal", "close_date": "2025-04-15", "probability": 0.45},
    "OPP-003": {"id": "OPP-003", "customer": "Tailspin Toys", "value": 510000.00, "stage": "qualification", "close_date": "2025-06-30", "probability": 0.25},
}

_PROJECTS: dict[str, dict] = {
    "PROJ-001": {"id": "PROJ-001", "name": "D365 ERP Implementation", "customer": "Contoso Ltd", "budget": 350000.00, "spent": 182000.00, "status": "in_progress", "completion_pct": 52},
    "PROJ-002": {"id": "PROJ-002", "name": "Supply Chain Automation", "customer": "Fabrikam Inc", "budget": 120000.00, "spent": 118500.00, "status": "at_risk", "completion_pct": 88},
}

_CUSTOMER_INTERACTIONS: dict[str, list[dict]] = {
    "Contoso Ltd": [
        {"type": "support_ticket", "sentiment": "negative", "date": "2025-01-10"},
        {"type": "renewal_call", "sentiment": "positive", "date": "2025-01-20"},
    ],
    "Fabrikam Inc": [
        {"type": "complaint", "sentiment": "negative", "date": "2025-01-05"},
        {"type": "complaint", "sentiment": "negative", "date": "2025-01-18"},
    ],
}


def forecast_revenue_pipeline(months_ahead: int = 3) -> dict[str, Any]:
    weighted_pipeline = sum(o["value"] * o["probability"] for o in _OPPORTUNITIES.values())
    monthly_forecast = []
    running = 0.0
    for i in range(1, months_ahead + 1):
        month = (datetime.utcnow() + timedelta(days=30 * i)).strftime("%Y-%m")
        monthly_opps = [
            o for o in _OPPORTUNITIES.values()
            if o["close_date"].startswith(month[:7])
        ]
        expected = sum(o["value"] * o["probability"] for o in monthly_opps)
        running += expected
        monthly_forecast.append({"month": month, "expected_revenue": round(expected, 2), "deals": len(monthly_opps)})
    return {
        "total_pipeline": sum(o["value"] for o in _OPPORTUNITIES.values()),
        "weighted_pipeline": round(weighted_pipeline, 2),
        "monthly_forecast": monthly_forecast,
        "generated_at": datetime.utcnow().isoformat(),
    }


def assess_deal_risk(opportunity_id: str) -> dict[str, Any]:
    opp = _OPPORTUNITIES.get(opportunity_id)
    if not opp:
        return {"error": f"Opportunity {opportunity_id} not found"}
    risks = []
    close_days = (datetime.strptime(opp["close_date"], "%Y-%m-%d") - datetime.utcnow()).days
    if close_days < 30 and opp["stage"] in ("qualification", "proposal"):
        risks.append({"factor": "stage_vs_close_date", "impact": "HIGH", "detail": "Deal stage too early for imminent close date"})
    if opp["probability"] < 0.50:
        risks.append({"factor": "low_probability", "impact": "MEDIUM", "detail": "Win probability below 50%"})
    interactions = _CUSTOMER_INTERACTIONS.get(opp["customer"], [])
    negative_sentiment = sum(1 for i in interactions if i["sentiment"] == "negative")
    if negative_sentiment >= 2:
        risks.append({"factor": "negative_sentiment", "impact": "HIGH", "detail": f"{negative_sentiment} recent negative customer interactions"})
    overall_risk = "HIGH" if any(r["impact"] == "HIGH" for r in risks) else "MEDIUM" if risks else "LOW"
    return {
        "opportunity_id": opportunity_id,
        "customer": opp["customer"],
        "deal_value": opp["value"],
        "current_stage": opp["stage"],
        "days_to_close": close_days,
        "overall_risk": overall_risk,
        "risk_factors": risks,
        "recommendation": "Escalate to senior sales" if overall_risk == "HIGH" else "Monitor weekly",
    }


def analyze_customer_retention(customer_name: str) -> dict[str, Any]:
    interactions = _CUSTOMER_INTERACTIONS.get(customer_name, [])
    if not interactions:
        return {"error": f"No interaction history for {customer_name}"}
    total = len(interactions)
    negative = sum(1 for i in interactions if i["sentiment"] == "negative")
    positive = total - negative
    churn_risk_score = min(100, int((negative / total) * 100) + random.randint(0, 10))
    return {
        "customer": customer_name,
        "total_interactions": total,
        "positive_interactions": positive,
        "negative_interactions": negative,
        "churn_risk_score": churn_risk_score,
        "churn_risk_level": "HIGH" if churn_risk_score > 60 else "MEDIUM" if churn_risk_score > 30 else "LOW",
        "recommended_actions": ["Executive business review", "Assign dedicated CSM"] if churn_risk_score > 60 else ["Quarterly check-in"],
    }


def get_project_health(project_id: str) -> dict[str, Any]:
    project = _PROJECTS.get(project_id)
    if not project:
        return {"error": f"Project {project_id} not found"}
    budget_utilization = project["spent"] / project["budget"]
    schedule_efficiency = project["completion_pct"] / (budget_utilization * 100) if budget_utilization else 0
    flags = []
    if budget_utilization > 0.90 and project["completion_pct"] < 90:
        flags.append("BUDGET_AT_RISK")
    if schedule_efficiency < 0.85:
        flags.append("BEHIND_SCHEDULE")
    return {
        "project_id": project_id,
        "name": project["name"],
        "customer": project["customer"],
        "budget": project["budget"],
        "spent": project["spent"],
        "budget_utilization_pct": round(budget_utilization * 100, 1),
        "completion_pct": project["completion_pct"],
        "schedule_efficiency_index": round(schedule_efficiency, 2),
        "status": project["status"],
        "flags": flags,
        "projected_final_cost": round(project["spent"] / (project["completion_pct"] / 100), 2) if project["completion_pct"] > 0 else None,
    }


def generate_invoice_from_milestone(project_id: str, milestone: str, amount: float) -> dict[str, Any]:
    project = _PROJECTS.get(project_id)
    if not project:
        return {"error": f"Project {project_id} not found"}
    invoice_id = f"PINV-{random.randint(1000, 9999)}"
    return {
        "invoice_id": invoice_id,
        "project_id": project_id,
        "customer": project["customer"],
        "milestone": milestone,
        "amount": amount,
        "due_date": (datetime.utcnow() + timedelta(days=30)).date().isoformat(),
        "status": "issued",
        "issued_at": datetime.utcnow().isoformat(),
    }
