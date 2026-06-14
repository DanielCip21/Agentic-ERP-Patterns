"""Simulated vendor risk tools: scoring, SLA tracking, smart contract payment triggers."""

from __future__ import annotations

import uuid
import random
from datetime import datetime
from typing import Any


_VENDORS: dict[str, dict] = {
    "VND-001": {
        "vendor_id": "VND-001",
        "name": "Apex Logistics SG",
        "category": "logistics",
        "country": "SG",
        "on_time_delivery_pct": 94.2,
        "avg_invoice_accuracy_pct": 98.1,
        "sla_breaches_ytd": 1,
        "contract_value_usd": 850_000,
        "payment_terms_days": 30,
        "active_contracts": ["CNT-101"],
    },
    "VND-002": {
        "vendor_id": "VND-002",
        "name": "CloudHW Japan",
        "category": "hardware",
        "country": "JP",
        "on_time_delivery_pct": 78.5,
        "avg_invoice_accuracy_pct": 91.0,
        "sla_breaches_ytd": 7,
        "contract_value_usd": 2_100_000,
        "payment_terms_days": 45,
        "active_contracts": ["CNT-102", "CNT-103"],
    },
    "VND-003": {
        "vendor_id": "VND-003",
        "name": "StudioOps AU",
        "category": "game_studio_services",
        "country": "AU",
        "on_time_delivery_pct": 88.0,
        "avg_invoice_accuracy_pct": 96.5,
        "sla_breaches_ytd": 3,
        "contract_value_usd": 560_000,
        "payment_terms_days": 30,
        "active_contracts": ["CNT-104"],
    },
}

_CONTRACTS: dict[str, dict] = {
    "CNT-101": {"contract_id": "CNT-101", "vendor_id": "VND-001", "value_usd": 850_000, "sla_threshold_pct": 90, "auto_pay_on_sla_met": True, "status": "active"},
    "CNT-102": {"contract_id": "CNT-102", "vendor_id": "VND-002", "value_usd": 1_200_000, "sla_threshold_pct": 85, "auto_pay_on_sla_met": False, "status": "active"},
    "CNT-103": {"contract_id": "CNT-103", "vendor_id": "VND-002", "value_usd": 900_000, "sla_threshold_pct": 85, "auto_pay_on_sla_met": True, "status": "active"},
    "CNT-104": {"contract_id": "CNT-104", "vendor_id": "VND-003", "value_usd": 560_000, "sla_threshold_pct": 88, "auto_pay_on_sla_met": True, "status": "active"},
}

_SMART_CONTRACT_PAYMENTS: list[dict] = []


def _compute_risk_score(vendor: dict) -> int:
    """Lower is better. 0-100."""
    score = 0
    score += max(0, (90 - vendor["on_time_delivery_pct"])) * 1.5
    score += max(0, (95 - vendor["avg_invoice_accuracy_pct"])) * 1.0
    score += vendor["sla_breaches_ytd"] * 4
    return min(int(score), 100)


def get_vendor_profile(vendor_id: str) -> dict[str, Any]:
    vendor = _VENDORS.get(vendor_id)
    if not vendor:
        return {"error": f"Vendor {vendor_id} not found"}
    return vendor


def score_vendor_risk(vendor_id: str) -> dict[str, Any]:
    vendor = _VENDORS.get(vendor_id)
    if not vendor:
        return {"error": f"Vendor {vendor_id} not found"}
    score = _compute_risk_score(vendor)
    if score >= 60:
        level, recommendation = "HIGH", "Consider contract review and alternative sourcing."
    elif score >= 30:
        level, recommendation = "MEDIUM", "Monitor SLA trends and schedule vendor review."
    else:
        level, recommendation = "LOW", "Vendor performing well. Eligible for preferred status."
    return {
        "vendor_id": vendor_id,
        "vendor_name": vendor["name"],
        "risk_score": score,
        "risk_level": level,
        "recommendation": recommendation,
        "scored_at": datetime.utcnow().isoformat(),
    }


def trigger_sla_payment(vendor_id: str, contract_id: str, amount_usd: float) -> dict[str, Any]:
    vendor = _VENDORS.get(vendor_id)
    contract = _CONTRACTS.get(contract_id)
    if not vendor:
        return {"error": f"Vendor {vendor_id} not found"}
    if not contract:
        return {"error": f"Contract {contract_id} not found"}
    if contract["vendor_id"] != vendor_id:
        return {"error": f"Contract {contract_id} does not belong to vendor {vendor_id}"}
    sla_met = vendor["on_time_delivery_pct"] >= contract["sla_threshold_pct"]
    if not sla_met:
        return {
            "vendor_id": vendor_id,
            "contract_id": contract_id,
            "payment_triggered": False,
            "reason": f"SLA not met: {vendor['on_time_delivery_pct']}% < {contract['sla_threshold_pct']}% threshold",
        }
    payment = {
        "payment_id": f"SCP-{uuid.uuid4().hex[:8].upper()}",
        "vendor_id": vendor_id,
        "contract_id": contract_id,
        "amount_usd": amount_usd,
        "sla_score_at_trigger": vendor["on_time_delivery_pct"],
        "status": "released",
        "smart_contract_tx": "0x" + uuid.uuid4().hex,
        "released_at": datetime.utcnow().isoformat(),
    }
    _SMART_CONTRACT_PAYMENTS.append(payment)
    return {**payment, "payment_triggered": True}
