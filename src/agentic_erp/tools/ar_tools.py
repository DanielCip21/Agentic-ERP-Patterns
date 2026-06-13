"""Simulated Accounts Receivable & Collections tools."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any


_CUSTOMERS: dict[str, dict] = {
    "CUST-001": {"id": "CUST-001", "name": "Tailspin Toys", "credit_limit": 50000.00, "credit_score": 91, "payment_history": "excellent"},
    "CUST-002": {"id": "CUST-002", "name": "Adventure Works", "credit_limit": 25000.00, "credit_score": 74, "payment_history": "good"},
    "CUST-003": {"id": "CUST-003", "name": "Wingtip Villas", "credit_limit": 10000.00, "credit_score": 55, "payment_history": "poor"},
}

_RECEIVABLES: dict[str, dict] = {
    "AR-001": {"id": "AR-001", "customer_id": "CUST-001", "amount": 15000.00, "due_date": "2025-01-31", "status": "open", "days_overdue": 0},
    "AR-002": {"id": "AR-002", "customer_id": "CUST-002", "amount": 8700.00, "due_date": "2025-01-15", "status": "overdue", "days_overdue": 20},
    "AR-003": {"id": "AR-003", "customer_id": "CUST-003", "amount": 4200.00, "due_date": "2024-12-31", "status": "overdue", "days_overdue": 45},
}


def forecast_collections(days_ahead: int = 30) -> dict[str, Any]:
    total_outstanding = sum(r["amount"] for r in _RECEIVABLES.values() if r["status"] != "paid")
    high_risk = sum(r["amount"] for r in _RECEIVABLES.values() if r["days_overdue"] > 30)
    medium_risk = sum(r["amount"] for r in _RECEIVABLES.values() if 0 < r["days_overdue"] <= 30)
    likely_collected = total_outstanding - high_risk * 0.6
    return {
        "forecast_period_days": days_ahead,
        "total_outstanding": total_outstanding,
        "likely_collected": round(likely_collected, 2),
        "high_risk_amount": high_risk,
        "medium_risk_amount": medium_risk,
        "collection_rate_forecast": round(likely_collected / total_outstanding * 100, 1) if total_outstanding else 0,
        "generated_at": datetime.utcnow().isoformat(),
    }


def score_customer_credit(customer_id: str) -> dict[str, Any]:
    customer = _CUSTOMERS.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}
    history_map = {"excellent": 20, "good": 10, "fair": 0, "poor": -10}
    adjusted_score = customer["credit_score"] + history_map.get(customer["payment_history"], 0)
    return {
        "customer_id": customer_id,
        "name": customer["name"],
        "base_credit_score": customer["credit_score"],
        "adjusted_score": min(100, adjusted_score),
        "credit_limit": customer["credit_limit"],
        "payment_history": customer["payment_history"],
        "risk_tier": "A" if adjusted_score >= 85 else "B" if adjusted_score >= 70 else "C",
        "recommended_action": "increase_limit" if adjusted_score >= 85 else "maintain" if adjusted_score >= 70 else "reduce_limit",
    }


def list_overdue_receivables(min_days_overdue: int = 0) -> list[dict[str, Any]]:
    overdue = [
        {**r, "customer_name": _CUSTOMERS.get(r["customer_id"], {}).get("name", "Unknown")}
        for r in _RECEIVABLES.values()
        if r["days_overdue"] >= min_days_overdue and r["status"] == "overdue"
    ]
    return sorted(overdue, key=lambda x: x["days_overdue"], reverse=True)


def apply_cash_payment(ar_id: str, payment_amount: float) -> dict[str, Any]:
    ar = _RECEIVABLES.get(ar_id)
    if not ar:
        return {"error": f"AR record {ar_id} not found"}
    if payment_amount >= ar["amount"]:
        _RECEIVABLES[ar_id]["status"] = "paid"
        remaining = round(payment_amount - ar["amount"], 2)
        _RECEIVABLES[ar_id]["amount"] = 0.0
    else:
        _RECEIVABLES[ar_id]["amount"] = round(ar["amount"] - payment_amount, 2)
        remaining = 0.0
    return {
        "ar_id": ar_id,
        "payment_applied": payment_amount,
        "remaining_balance": _RECEIVABLES[ar_id]["amount"],
        "status": _RECEIVABLES[ar_id]["status"],
        "overpayment": remaining,
        "applied_at": datetime.utcnow().isoformat(),
    }


def generate_collection_reminder(customer_id: str) -> dict[str, Any]:
    customer = _CUSTOMERS.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}
    open_items = [r for r in _RECEIVABLES.values() if r["customer_id"] == customer_id and r["status"] != "paid"]
    total_due = sum(r["amount"] for r in open_items)
    urgency = "URGENT" if any(r["days_overdue"] > 30 for r in open_items) else "STANDARD"
    return {
        "customer_id": customer_id,
        "customer_name": customer["name"],
        "open_invoices": len(open_items),
        "total_due": total_due,
        "urgency": urgency,
        "message": f"Dear {customer['name']}, you have {len(open_items)} outstanding invoice(s) totaling ${total_due:,.2f}. Please remit payment at your earliest convenience.",
        "generated_at": datetime.utcnow().isoformat(),
    }
