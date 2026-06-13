"""Simulated Supply Chain & Procurement tools."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any


_SUPPLIERS: dict[str, dict] = {
    "SUP-001": {"id": "SUP-001", "name": "Apex Manufacturing", "lead_time_days": 7, "reliability": 0.97, "unit_cost_index": 0.92, "country": "US"},
    "SUP-002": {"id": "SUP-002", "name": "Global Parts Ltd", "lead_time_days": 14, "reliability": 0.88, "unit_cost_index": 0.78, "country": "CN"},
    "SUP-003": {"id": "SUP-003", "name": "EuroPrecision GmbH", "lead_time_days": 10, "reliability": 0.94, "unit_cost_index": 1.05, "country": "DE"},
}

_DEMAND_HISTORY: list[dict] = [
    {"month": "2024-10", "sku": "SKU-A", "units_sold": 420},
    {"month": "2024-11", "sku": "SKU-A", "units_sold": 510},
    {"month": "2024-12", "sku": "SKU-A", "units_sold": 680},
    {"month": "2025-01", "sku": "SKU-A", "units_sold": 390},
]

_LOGISTICS: dict[str, dict] = {
    "SHIP-001": {"id": "SHIP-001", "carrier": "FedEx Freight", "status": "in_transit", "origin": "Chicago", "destination": "LA", "eta": "2025-02-08"},
    "SHIP-002": {"id": "SHIP-002", "carrier": "UPS Supply Chain", "status": "delivered", "origin": "NY", "destination": "Miami", "eta": "2025-01-30"},
}


def select_optimal_supplier(sku: str, quantity: int, priority: str = "balanced") -> dict[str, Any]:
    scored = []
    for sup in _SUPPLIERS.values():
        if priority == "cost":
            score = (1 - sup["unit_cost_index"]) * 0.7 + sup["reliability"] * 0.3
        elif priority == "speed":
            lead_score = 1 - (sup["lead_time_days"] / 30)
            score = lead_score * 0.7 + sup["reliability"] * 0.3
        else:
            lead_score = 1 - (sup["lead_time_days"] / 30)
            score = sup["reliability"] * 0.4 + (1 - sup["unit_cost_index"]) * 0.3 + lead_score * 0.3
        scored.append({**sup, "composite_score": round(score, 3)})
    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    winner = scored[0]
    return {
        "sku": sku,
        "quantity": quantity,
        "recommended_supplier": winner["id"],
        "supplier_name": winner["name"],
        "score": winner["composite_score"],
        "estimated_delivery_days": winner["lead_time_days"],
        "all_suppliers_ranked": scored,
    }


def forecast_demand(sku: str, months_ahead: int = 3) -> dict[str, Any]:
    history = [d["units_sold"] for d in _DEMAND_HISTORY if d["sku"] == sku]
    if not history:
        return {"error": f"No demand history for SKU {sku}"}
    avg = sum(history) / len(history)
    trend = (history[-1] - history[0]) / max(len(history) - 1, 1)
    forecasts = []
    for i in range(1, months_ahead + 1):
        projected = max(0, round(avg + trend * i * 0.5 + random.uniform(-20, 20)))
        month = (datetime.utcnow() + timedelta(days=30 * i)).strftime("%Y-%m")
        forecasts.append({"month": month, "forecasted_units": projected})
    return {
        "sku": sku,
        "historical_avg": round(avg, 1),
        "trend_per_month": round(trend, 1),
        "forecast": forecasts,
        "total_forecasted": sum(f["forecasted_units"] for f in forecasts),
        "model": "AI-ARIMA-v3",
    }


def track_shipment(shipment_id: str) -> dict[str, Any]:
    shipment = _LOGISTICS.get(shipment_id)
    if not shipment:
        return {"error": f"Shipment {shipment_id} not found"}
    eta_date = datetime.strptime(shipment["eta"], "%Y-%m-%d")
    days_remaining = (eta_date - datetime.utcnow()).days
    return {
        **shipment,
        "days_until_eta": max(0, days_remaining),
        "delay_risk": "HIGH" if days_remaining < 0 else "LOW",
        "tracked_at": datetime.utcnow().isoformat(),
    }


def assess_supply_chain_risk(supplier_id: str) -> dict[str, Any]:
    supplier = _SUPPLIERS.get(supplier_id)
    if not supplier:
        return {"error": f"Supplier {supplier_id} not found"}
    risks = []
    if supplier["reliability"] < 0.90:
        risks.append({"type": "reliability", "severity": "MEDIUM", "detail": "Delivery reliability below 90%"})
    if supplier["lead_time_days"] > 12:
        risks.append({"type": "lead_time", "severity": "LOW", "detail": "Long lead time increases buffer stock requirements"})
    geo_risks = {"CN": "HIGH", "DE": "LOW", "US": "LOW"}
    geo_risk = geo_risks.get(supplier["country"], "MEDIUM")
    if geo_risk == "HIGH":
        risks.append({"type": "geopolitical", "severity": "HIGH", "detail": f"Operations in {supplier['country']} carry elevated trade risk"})
    overall = "HIGH" if any(r["severity"] == "HIGH" for r in risks) else "MEDIUM" if risks else "LOW"
    return {
        "supplier_id": supplier_id,
        "supplier_name": supplier["name"],
        "overall_risk": overall,
        "risk_factors": risks,
        "mitigation": "Dual-source this supplier" if overall == "HIGH" else "Monitor quarterly",
    }


def optimize_freight_cost(origin: str, destination: str, weight_kg: float) -> dict[str, Any]:
    carriers = [
        {"carrier": "FedEx Freight", "rate_per_kg": 2.40, "transit_days": 3},
        {"carrier": "UPS Supply Chain", "rate_per_kg": 2.15, "transit_days": 4},
        {"carrier": "DHL Express", "rate_per_kg": 3.10, "transit_days": 2},
    ]
    options = [
        {**c, "total_cost": round(c["rate_per_kg"] * weight_kg, 2)}
        for c in carriers
    ]
    options.sort(key=lambda x: x["total_cost"])
    return {
        "origin": origin,
        "destination": destination,
        "weight_kg": weight_kg,
        "optimal_carrier": options[0]["carrier"],
        "optimal_cost": options[0]["total_cost"],
        "transit_days": options[0]["transit_days"],
        "all_options": options,
    }
