"""Simulated finance backend — AR/AP, expense categorization, payment scheduling."""

from __future__ import annotations

import random
from datetime import datetime, date, timedelta
from typing import Any

_INVOICES: dict[str, dict] = {
    "INV-2001": {"id": "INV-2001", "customer": "Contoso Ltd", "amount": 12500.00, "due_date": "2026-05-15", "status": "overdue", "days_overdue": 29},
    "INV-2002": {"id": "INV-2002", "customer": "Fabrikam Inc", "amount": 4300.00, "due_date": "2026-06-01", "status": "overdue", "days_overdue": 12},
    "INV-2003": {"id": "INV-2003", "customer": "Northwind", "amount": 8900.00, "due_date": "2026-06-20", "status": "open", "days_overdue": 0},
}

_PAYMENTS: list[dict] = []

_EXPENSE_CATEGORIES = {
    "office": ["supplies", "furniture", "equipment", "stationery"],
    "travel": ["flight", "hotel", "taxi", "mileage", "meal", "conference"],
    "software": ["subscription", "license", "saas", "cloud", "aws", "azure"],
    "utilities": ["electricity", "internet", "phone", "water"],
    "marketing": ["advertising", "campaign", "social media", "seo"],
}

_ACCOUNTS: dict[str, dict] = {
    "ACC-1001": {"id": "ACC-1001", "name": "Accounts Receivable", "balance": 25700.00, "currency": "USD"},
    "ACC-1002": {"id": "ACC-1002", "name": "Accounts Payable", "balance": -8200.00, "currency": "USD"},
    "ACC-1003": {"id": "ACC-1003", "name": "Operating Expenses", "balance": -45000.00, "currency": "USD"},
}


def list_outstanding_invoices(days_overdue: int = 0) -> list[dict[str, Any]]:
    return [
        inv for inv in _INVOICES.values()
        if inv["days_overdue"] >= days_overdue
    ]


def categorize_expense(description: str, amount: float) -> dict[str, Any]:
    desc_lower = description.lower()
    matched_category = "uncategorized"
    confidence = 0.5
    for category, keywords in _EXPENSE_CATEGORIES.items():
        if any(kw in desc_lower for kw in keywords):
            matched_category = category
            confidence = 0.92
            break
    return {
        "description": description,
        "amount": amount,
        "category": matched_category,
        "confidence": confidence,
        "tax_deductible": matched_category in {"travel", "software", "marketing"},
        "categorized_at": datetime.utcnow().isoformat(),
    }


def schedule_payment(invoice_id: str, payment_date: str) -> dict[str, Any]:
    invoice = _INVOICES.get(invoice_id)
    if not invoice:
        return {"error": f"Invoice {invoice_id} not found"}
    payment = {
        "payment_id": f"PAY-{random.randint(10000, 99999)}",
        "invoice_id": invoice_id,
        "amount": invoice["amount"],
        "scheduled_date": payment_date,
        "status": "scheduled",
        "created_at": datetime.utcnow().isoformat(),
    }
    _PAYMENTS.append(payment)
    _INVOICES[invoice_id]["status"] = "payment_scheduled"
    return payment


def reconcile_account(account_id: str) -> dict[str, Any]:
    account = _ACCOUNTS.get(account_id)
    if not account:
        return {"error": f"Account {account_id} not found"}
    discrepancies = random.randint(0, 3)
    return {
        "account_id": account_id,
        "account_name": account["name"],
        "book_balance": account["balance"],
        "statement_balance": round(account["balance"] + random.uniform(-50, 50), 2),
        "discrepancies_found": discrepancies,
        "status": "reconciled" if discrepancies == 0 else "requires_review",
        "reconciled_at": datetime.utcnow().isoformat(),
    }
