"""Simulated ERP tool implementations (swap for real Dynamics 365 / Dataverse calls)."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any


_ORDERS: dict[str, dict] = {
    "ORD-001": {"id": "ORD-001", "customer": "Contoso Ltd", "status": "pending", "total": 4200.00, "items": [{"sku": "SKU-A", "qty": 10}]},
    "ORD-002": {"id": "ORD-002", "customer": "Fabrikam Inc", "status": "processing", "total": 1850.50, "items": [{"sku": "SKU-B", "qty": 5}]},
}

_INVENTORY: dict[str, dict] = {
    "SKU-A": {"sku": "SKU-A", "name": "Widget Alpha", "on_hand": 45, "reorder_point": 20, "reorder_qty": 100},
    "SKU-B": {"sku": "SKU-B", "name": "Gadget Beta", "on_hand": 8, "reorder_point": 15, "reorder_qty": 50},
    "SKU-C": {"sku": "SKU-C", "name": "Component Gamma", "on_hand": 120, "reorder_point": 30, "reorder_qty": 200},
}

_PURCHASE_ORDERS: list[dict] = []


def get_order(order_id: str) -> dict[str, Any]:
    order = _ORDERS.get(order_id)
    if not order:
        return {"error": f"Order {order_id} not found"}
    return order


def update_order_status(order_id: str, status: str) -> dict[str, Any]:
    valid_statuses = {"pending", "processing", "shipped", "delivered", "cancelled"}
    if status not in valid_statuses:
        return {"error": f"Invalid status '{status}'. Must be one of {valid_statuses}"}
    if order_id not in _ORDERS:
        return {"error": f"Order {order_id} not found"}
    _ORDERS[order_id]["status"] = status
    return {"order_id": order_id, "status": status, "updated_at": datetime.utcnow().isoformat()}


def check_inventory(sku: str) -> dict[str, Any]:
    item = _INVENTORY.get(sku)
    if not item:
        return {"error": f"SKU {sku} not found"}
    return {**item, "below_reorder_point": item["on_hand"] < item["reorder_point"]}


def list_low_stock_items() -> list[dict[str, Any]]:
    return [
        {**item, "shortage": item["reorder_point"] - item["on_hand"]}
        for item in _INVENTORY.values()
        if item["on_hand"] < item["reorder_point"]
    ]


def create_purchase_order(sku: str, quantity: int, supplier: str = "Default Supplier") -> dict[str, Any]:
    if sku not in _INVENTORY:
        return {"error": f"SKU {sku} not found"}
    po = {
        "po_id": f"PO-{random.randint(1000, 9999)}",
        "sku": sku,
        "quantity": quantity,
        "supplier": supplier,
        "estimated_delivery": (datetime.utcnow() + timedelta(days=7)).date().isoformat(),
        "status": "submitted",
    }
    _PURCHASE_ORDERS.append(po)
    _INVENTORY[sku]["on_hand"] += quantity  # optimistic update for simulation
    return po
