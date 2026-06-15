"""Simulated procurement backend — vendor management, RFQs, POs, 3-way match."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

_VENDORS: dict[str, dict] = {
    "VND-001": {
        "id": "VND-001",
        "name": "Acme Supplies",
        "category": "raw_materials",
        "rating": 4.5,
        "contact": "acme@example.com",
    },
    "VND-002": {
        "id": "VND-002",
        "name": "Beta Components",
        "category": "electronics",
        "rating": 4.2,
        "contact": "beta@example.com",
    },
    "VND-003": {
        "id": "VND-003",
        "name": "Gamma Packaging",
        "category": "packaging",
        "rating": 3.8,
        "contact": "gamma@example.com",
    },
    "VND-004": {
        "id": "VND-004",
        "name": "Delta Raw Goods",
        "category": "raw_materials",
        "rating": 4.7,
        "contact": "delta@example.com",
    },
}

_RFQS: dict[str, dict] = {}
_PURCHASE_ORDERS: dict[str, dict] = {}
_INVOICES: dict[str, dict] = {
    "INV-001": {
        "id": "INV-001",
        "po_id": "PO-1001",
        "vendor": "VND-001",
        "amount": 5000.00,
        "status": "pending",
    },
    "INV-002": {
        "id": "INV-002",
        "po_id": "PO-1002",
        "vendor": "VND-002",
        "amount": 3200.00,
        "status": "pending",
    },
}


def search_vendors(category: str, min_rating: float = 0.0) -> list[dict[str, Any]]:
    results = [
        v
        for v in _VENDORS.values()
        if v["category"] == category and v["rating"] >= min_rating
    ]
    return results or [
        {
            "message": f"No vendors found for category '{category}' with rating >= {min_rating}"
        }
    ]


def create_rfq(vendor_ids: list[str], items: list[dict]) -> dict[str, Any]:
    rfq_id = f"RFQ-{random.randint(1000, 9999)}"
    rfq = {
        "rfq_id": rfq_id,
        "vendor_ids": vendor_ids,
        "items": items,
        "status": "sent",
        "created_at": datetime.utcnow().isoformat(),
        "response_deadline": (datetime.utcnow() + timedelta(days=5)).date().isoformat(),
    }
    _RFQS[rfq_id] = rfq
    return rfq


def create_purchase_order(
    vendor_id: str, items: list[dict], total: float
) -> dict[str, Any]:
    if vendor_id not in _VENDORS:
        return {"error": f"Vendor {vendor_id} not found"}
    po_id = f"PO-{random.randint(1000, 9999)}"
    po = {
        "po_id": po_id,
        "vendor_id": vendor_id,
        "vendor_name": _VENDORS[vendor_id]["name"],
        "items": items,
        "total": total,
        "status": "approved",
        "expected_delivery": (datetime.utcnow() + timedelta(days=14))
        .date()
        .isoformat(),
        "created_at": datetime.utcnow().isoformat(),
    }
    _PURCHASE_ORDERS[po_id] = po
    return po


def match_invoice_to_po(invoice_id: str, po_id: str) -> dict[str, Any]:
    invoice = _INVOICES.get(invoice_id)
    if not invoice:
        return {"error": f"Invoice {invoice_id} not found"}
    po = _PURCHASE_ORDERS.get(po_id) or {
        "po_id": po_id,
        "total": invoice["amount"] + random.uniform(-100, 100),
    }
    variance = abs(invoice["amount"] - po["total"])
    match_result = "matched" if variance < 50 else "discrepancy"
    invoice["status"] = match_result
    return {
        "invoice_id": invoice_id,
        "po_id": po_id,
        "invoice_amount": invoice["amount"],
        "po_amount": po["total"],
        "variance": round(variance, 2),
        "match_result": match_result,
        "matched_at": datetime.utcnow().isoformat(),
    }
