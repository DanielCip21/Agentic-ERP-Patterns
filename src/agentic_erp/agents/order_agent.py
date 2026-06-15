"""Pattern: Tool-use agent for ERP order lifecycle management."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import erp_tools

_TOOLS = [
    {
        "name": "get_order",
        "description": "Retrieve full order details by order ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The ERP order ID (e.g. ORD-001)",
                },
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "update_order_status",
        "description": "Update the status of an order. Valid statuses: pending, processing, shipped, delivered, cancelled.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "status": {"type": "string"},
            },
            "required": ["order_id", "status"],
        },
    },
    {
        "name": "check_inventory",
        "description": "Check current inventory level for a given SKU.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {"type": "string", "description": "The product SKU"},
            },
            "required": ["sku"],
        },
    },
]

_SYSTEM_PROMPT = """You are an ERP Order Processing Agent for a manufacturing company.
Your job is to manage order lifecycle: retrieve order details, verify inventory availability,
and update order statuses appropriately. Always confirm inventory before marking an order
as 'processing'. Be concise and factual in your responses."""


class OrderProcessingAgent(BaseERPAgent):
    """Manages order lifecycle using ERP tools."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_order":
                return erp_tools.get_order(**inputs)
            case "update_order_status":
                return erp_tools.update_order_status(**inputs)
            case "check_inventory":
                return erp_tools.check_inventory(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
