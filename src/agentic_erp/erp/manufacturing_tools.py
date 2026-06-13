"""Simulated manufacturing backend — production scheduling, BOM, work orders, capacity."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

_PRODUCTION_SCHEDULE: list[dict] = [
    {"product_id": "PROD-001", "product_name": "Widget Alpha", "quantity": 500, "start_date": "2026-06-15", "end_date": "2026-06-20", "status": "planned"},
    {"product_id": "PROD-002", "product_name": "Gadget Beta", "quantity": 200, "start_date": "2026-06-18", "end_date": "2026-06-22", "status": "in_progress"},
]

_BOMS: dict[str, list] = {
    "PROD-001": [
        {"component": "COMP-A", "description": "Aluminium Frame", "qty_per_unit": 2, "lead_time_days": 5},
        {"component": "COMP-B", "description": "Circuit Board", "qty_per_unit": 1, "lead_time_days": 10},
        {"component": "COMP-C", "description": "Fasteners Pack", "qty_per_unit": 8, "lead_time_days": 2},
    ],
    "PROD-002": [
        {"component": "COMP-D", "description": "Steel Housing", "qty_per_unit": 1, "lead_time_days": 7},
        {"component": "COMP-E", "description": "Motor Unit", "qty_per_unit": 1, "lead_time_days": 14},
    ],
}

_WORK_ORDERS: list[dict] = []

_WORKCENTERS: dict[str, dict] = {
    "WC-001": {"id": "WC-001", "name": "Assembly Line A", "capacity_units_per_day": 100},
    "WC-002": {"id": "WC-002", "name": "CNC Machining", "capacity_units_per_day": 50},
    "WC-003": {"id": "WC-003", "name": "Quality Control", "capacity_units_per_day": 200},
}


def get_production_schedule() -> list[dict[str, Any]]:
    return _PRODUCTION_SCHEDULE


def explode_bom(product_id: str, quantity: int) -> dict[str, Any]:
    bom = _BOMS.get(product_id)
    if not bom:
        return {"error": f"BOM not found for product {product_id}"}
    exploded = [
        {
            **component,
            "total_qty_required": component["qty_per_unit"] * quantity,
            "order_by_date": (datetime.utcnow() + timedelta(days=component["lead_time_days"])).date().isoformat(),
        }
        for component in bom
    ]
    return {
        "product_id": product_id,
        "production_quantity": quantity,
        "components": exploded,
        "total_components": len(exploded),
    }


def create_work_order(product_id: str, quantity: int, due_date: str) -> dict[str, Any]:
    wo_id = f"WO-{random.randint(10000, 99999)}"
    work_order = {
        "wo_id": wo_id,
        "product_id": product_id,
        "quantity": quantity,
        "due_date": due_date,
        "status": "released",
        "workcenter": "WC-001",
        "estimated_hours": round(quantity * 0.5, 1),
        "created_at": datetime.utcnow().isoformat(),
    }
    _WORK_ORDERS.append(work_order)
    return work_order


def check_capacity(workcenter_id: str, date: str) -> dict[str, Any]:
    wc = _WORKCENTERS.get(workcenter_id)
    if not wc:
        return {"error": f"Workcenter {workcenter_id} not found"}
    scheduled_load = random.randint(30, 110)
    available = max(0, wc["capacity_units_per_day"] - scheduled_load)
    return {
        "workcenter_id": workcenter_id,
        "workcenter_name": wc["name"],
        "date": date,
        "capacity_units_per_day": wc["capacity_units_per_day"],
        "scheduled_load": scheduled_load,
        "available_capacity": available,
        "utilization_pct": round(scheduled_load / wc["capacity_units_per_day"] * 100, 1),
        "status": "overloaded" if scheduled_load > wc["capacity_units_per_day"] else "available",
    }
