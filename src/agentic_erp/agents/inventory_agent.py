"""Pattern: Tool-use agent for automated inventory replenishment."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import erp_tools

_TOOLS = [
    {
        "name": "list_low_stock_items",
        "description": "List all inventory items that are at or below their reorder point.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "check_inventory",
        "description": "Check current inventory level for a specific SKU.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {"type": "string"},
            },
            "required": ["sku"],
        },
    },
    {
        "name": "create_purchase_order",
        "description": "Create a purchase order to replenish stock for a SKU.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {"type": "string", "description": "Product SKU to reorder"},
                "quantity": {"type": "integer", "description": "Quantity to order"},
                "supplier": {"type": "string", "description": "Supplier name (optional)"},
            },
            "required": ["sku", "quantity"],
        },
    },
]

_SYSTEM_PROMPT = """You are an ERP Inventory Management Agent.
Your job is to monitor stock levels and automatically create purchase orders for items
below their reorder point. Use the item's configured reorder_qty when creating POs.
Summarise all actions taken at the end."""


class InventoryAgent(BaseERPAgent):
    """Monitors inventory and triggers replenishment purchase orders."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "list_low_stock_items":
                return erp_tools.list_low_stock_items()
            case "check_inventory":
                return erp_tools.check_inventory(**inputs)
            case "create_purchase_order":
                return erp_tools.create_purchase_order(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
