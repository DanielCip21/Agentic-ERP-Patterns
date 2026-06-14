"""Simulated Accounts Payable & Vendor Management tools."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any


_VENDORS: dict[str, dict] = {
    "VND-001": {"id": "VND-001", "name": "Contoso Supplies", "credit_score": 88, "on_time_rate": 0.96, "risk": "low", "payment_terms": "Net-30"},
    "VND-002": {"id": "VND-002", "name": "Fabrikam Parts", "credit_score": 72, "on_time_rate": 0.84, "risk": "medium", "payment_terms": "Net-45"},
    "VND-003": {"id": "VND-003", "name": "Northwind Logistics", "credit_score": 61, "on_time_rate": 0.71, "risk": "high", "payment_terms": "Net-60"},
}

_INVOICES: dict[str, dict] = {
    "INV-001": {"id": "INV-001", "vendor_id": "VND-001", "amount": 12500.00, "status": "pending", "due_date": "2025-02-15", "po_id": "PO-1001", "receipt_id": "REC-501"},
    "INV-002": {"id": "INV-002", "vendor_id": "VND-002", "amount": 8300.00, "status": "approved", "due_date": "2025-02-20", "po_id": "PO-1002", "receipt_id": "REC-502"},
    "INV-003": {"id": "INV-003", "vendor_id": "VND-001", "amount": 12500.00, "status": "pending", "due_date": "2025-02-25", "po_id": "PO-1003", "receipt_id": "REC-503"},
}

_PURCHASE_ORDERS: dict[str, dict] = {
    "PO-1001": {"id": "PO-1001", "vendor_id": "VND-001", "amount": 12500.00, "items": [{"sku": "SKU-A", "qty": 100}]},
    "PO-1002": {"id": "PO-1002", "vendor_id": "VND-002", "amount": 8300.00, "items": [{"sku": "SKU-B", "qty": 50}]},
    "PO-1003": {"id": "PO-1003", "vendor_id": "VND-001", "amount": 12400.00, "items": [{"sku": "SKU-A", "qty": 99}]},
}


def detect_duplicate_invoices() -> list[dict[str, Any]]:
    seen: dict[str, list[str]] = {}
    for inv in _INVOICES.values():
        key = f"{inv['vendor_id']}:{inv['amount']}"
        seen.setdefault(key, []).append(inv["id"])
    duplicates = [
        {"invoice_ids": ids, "vendor_id": key.split(":")[0], "amount": float(key.split(":")[1]), "risk": "HIGH"}
        for key, ids in seen.items()
        if len(ids) > 1
    ]
    return duplicates if duplicates else [{"message": "No duplicate invoices detected"}]


def three_way_match(invoice_id: str) -> dict[str, Any]:
    invoice = _INVOICES.get(invoice_id)
    if not invoice:
        return {"error": f"Invoice {invoice_id} not found"}
    po = _PURCHASE_ORDERS.get(invoice["po_id"])
    match = po and abs(po["amount"] - invoice["amount"]) < invoice["amount"] * 0.02
    return {
        "invoice_id": invoice_id,
        "po_id": invoice["po_id"],
        "receipt_id": invoice["receipt_id"],
        "invoice_amount": invoice["amount"],
        "po_amount": po["amount"] if po else None,
        "match_result": "MATCHED" if match else "MISMATCH",
        "variance": abs(po["amount"] - invoice["amount"]) if po else None,
        "approved_for_payment": match,
    }


def score_vendor(vendor_id: str) -> dict[str, Any]:
    vendor = _VENDORS.get(vendor_id)
    if not vendor:
        return {"error": f"Vendor {vendor_id} not found"}
    score = round((vendor["credit_score"] * 0.5) + (vendor["on_time_rate"] * 100 * 0.5), 1)
    return {
        "vendor_id": vendor_id,
        "name": vendor["name"],
        "composite_score": score,
        "credit_score": vendor["credit_score"],
        "on_time_delivery_rate": vendor["on_time_rate"],
        "risk_rating": vendor["risk"],
        "recommendation": "preferred" if score > 85 else "review" if score > 70 else "watchlist",
    }


def list_invoices_due(days_ahead: int = 30) -> list[dict[str, Any]]:
    cutoff = datetime.utcnow() + timedelta(days=days_ahead)
    result = []
    for inv in _INVOICES.values():
        due = datetime.strptime(inv["due_date"], "%Y-%m-%d")
        if due <= cutoff and inv["status"] != "paid":
            result.append({**inv, "days_until_due": (due - datetime.utcnow()).days})
    return result


def approve_invoice(invoice_id: str) -> dict[str, Any]:
    invoice = _INVOICES.get(invoice_id)
    if not invoice:
        return {"error": f"Invoice {invoice_id} not found"}
    _INVOICES[invoice_id]["status"] = "approved"
    return {"invoice_id": invoice_id, "status": "approved", "approved_at": datetime.utcnow().isoformat()}


def calculate_dynamic_discount(invoice_id: str, pay_in_days: int) -> dict[str, Any]:
    invoice = _INVOICES.get(invoice_id)
    if not invoice:
        return {"error": f"Invoice {invoice_id} not found"}
    discount_rate = max(0.0, 0.02 - (pay_in_days * 0.0005))
    savings = round(invoice["amount"] * discount_rate, 2)
    return {
        "invoice_id": invoice_id,
        "original_amount": invoice["amount"],
        "pay_in_days": pay_in_days,
        "discount_rate": round(discount_rate, 4),
        "savings": savings,
        "net_payment": round(invoice["amount"] - savings, 2),
    }
