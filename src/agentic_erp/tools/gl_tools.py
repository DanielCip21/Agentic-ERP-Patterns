"""Simulated General Ledger tools (swap for real Dynamics 365 GL API calls)."""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any


_JOURNAL_ENTRIES: list[dict] = [
    {"id": "JE-001", "account": "1000", "debit": 5000.00, "credit": 0.0, "description": "Cash receipt", "status": "posted", "period": "2025-01"},
    {"id": "JE-002", "account": "2000", "debit": 0.0, "credit": 5000.00, "description": "Revenue recognition", "status": "posted", "period": "2025-01"},
    {"id": "JE-003", "account": "6000", "debit": 1200.00, "credit": 0.0, "description": "Marketing expense", "status": "pending", "period": "2025-01"},
    {"id": "JE-004", "account": "6100", "debit": 800.00, "credit": 0.0, "description": "Rent expense", "status": "pending", "period": "2025-01"},
]

_ACCOUNTS: dict[str, dict] = {
    "1000": {"account": "1000", "name": "Cash", "type": "asset", "balance": 125000.00},
    "1100": {"account": "1100", "name": "Accounts Receivable", "type": "asset", "balance": 84500.00},
    "2000": {"account": "2000", "name": "Revenue", "type": "revenue", "balance": 450000.00},
    "3000": {"account": "3000", "name": "Cost of Goods Sold", "type": "expense", "balance": 210000.00},
    "4000": {"account": "4000", "name": "Retained Earnings", "type": "equity", "balance": 95000.00},
    "6000": {"account": "6000", "name": "Marketing Expense", "type": "expense", "balance": 32000.00},
    "6100": {"account": "6100", "name": "Rent Expense", "type": "expense", "balance": 48000.00},
}

_BUDGETS: dict[str, dict] = {
    "2025-Q1": {"period": "2025-Q1", "revenue": 500000.00, "cogs": 220000.00, "opex": 85000.00, "net_income": 195000.00},
    "2025-Q2": {"period": "2025-Q2", "revenue": 520000.00, "cogs": 228000.00, "opex": 87000.00, "net_income": 205000.00},
}


def reconcile_gl_accounts(period: str) -> dict[str, Any]:
    entries = [e for e in _JOURNAL_ENTRIES if e["period"] == period]
    total_debits = sum(e["debit"] for e in entries)
    total_credits = sum(e["credit"] for e in entries)
    mismatch = abs(total_debits - total_credits)
    flagged = [e for e in entries if e["status"] == "pending"]
    return {
        "period": period,
        "total_debits": total_debits,
        "total_credits": total_credits,
        "balanced": mismatch < 0.01,
        "mismatch_amount": mismatch,
        "pending_entries": len(flagged),
        "anomalies_detected": len(flagged),
        "reconciled_at": datetime.utcnow().isoformat(),
    }


def detect_financial_anomalies(account: str | None = None) -> list[dict[str, Any]]:
    anomalies = []
    entries = _JOURNAL_ENTRIES if account is None else [e for e in _JOURNAL_ENTRIES if e["account"] == account]
    for entry in entries:
        if entry["debit"] > 2000 and entry["status"] == "pending":
            anomalies.append({
                "entry_id": entry["id"],
                "account": entry["account"],
                "risk": "high",
                "reason": "Large pending debit exceeds threshold",
                "amount": entry["debit"],
            })
    if not anomalies:
        anomalies.append({"message": "No anomalies detected", "account": account or "all"})
    return anomalies


def categorize_expenses(description: str, amount: float) -> dict[str, Any]:
    keywords = {
        "rent": "6100", "office": "6100",
        "marketing": "6000", "advertising": "6000",
        "salary": "5000", "payroll": "5000",
        "travel": "6200", "meals": "6200",
    }
    account = "6999"
    for kw, acct in keywords.items():
        if kw in description.lower():
            account = acct
            break
    return {
        "description": description,
        "amount": amount,
        "suggested_account": account,
        "confidence": round(random.uniform(0.82, 0.99), 2),
        "categorized_by": "AI-ML-Classifier-v2",
    }


def get_budget_vs_actual(period: str) -> dict[str, Any]:
    budget = _BUDGETS.get(period)
    if not budget:
        return {"error": f"No budget found for period {period}"}
    actual_revenue = _ACCOUNTS["2000"]["balance"]
    actual_cogs = _ACCOUNTS["3000"]["balance"]
    actual_opex = _ACCOUNTS["6000"]["balance"] + _ACCOUNTS["6100"]["balance"]
    return {
        "period": period,
        "revenue": {"budget": budget["revenue"], "actual": actual_revenue, "variance": actual_revenue - budget["revenue"]},
        "cogs": {"budget": budget["cogs"], "actual": actual_cogs, "variance": actual_cogs - budget["cogs"]},
        "opex": {"budget": budget["opex"], "actual": actual_opex, "variance": actual_opex - budget["opex"]},
    }


def post_journal_entry(account: str, debit: float, credit: float, description: str) -> dict[str, Any]:
    entry_id = f"JE-{random.randint(100, 999)}"
    entry = {
        "id": entry_id,
        "account": account,
        "debit": debit,
        "credit": credit,
        "description": description,
        "status": "posted",
        "period": datetime.utcnow().strftime("%Y-%m"),
    }
    _JOURNAL_ENTRIES.append(entry)
    if account in _ACCOUNTS:
        _ACCOUNTS[account]["balance"] += (debit - credit)
    return {**entry, "posted_at": datetime.utcnow().isoformat()}


def get_trial_balance() -> list[dict[str, Any]]:
    return [
        {
            "account": acct["account"],
            "name": acct["name"],
            "type": acct["type"],
            "balance": acct["balance"],
        }
        for acct in _ACCOUNTS.values()
    ]
