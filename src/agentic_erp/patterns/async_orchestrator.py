"""Pattern: Concurrent multi-agent orchestration using asyncio.

Runs specialist agents in parallel rather than sequentially, cutting wall-clock
time proportionally to the number of agents dispatched.
"""

from __future__ import annotations

import asyncio

import anthropic

from agentic_erp.agents.async_base import AsyncBaseERPAgent
from agentic_erp.tools import erp_tools

import json
from typing import Any


class AsyncOrderAgent(AsyncBaseERPAgent):
    _TOOLS = [
        {"name": "get_order", "description": "Retrieve order details.", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}},
        {"name": "update_order_status", "description": "Update order status.", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}, "status": {"type": "string"}}, "required": ["order_id", "status"]}},
        {"name": "check_inventory", "description": "Check inventory for a SKU.", "input_schema": {"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]}},
    ]
    _SYSTEM = "You are an async ERP Order Agent. Manage order lifecycle efficiently."

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=self._TOOLS, system_prompt=self._SYSTEM, **kwargs)

    async def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_order":
                return erp_tools.get_order(**inputs)
            case "update_order_status":
                return erp_tools.update_order_status(**inputs)
            case "check_inventory":
                return erp_tools.check_inventory(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}


class AsyncInventoryAgent(AsyncBaseERPAgent):
    _TOOLS = [
        {"name": "list_low_stock_items", "description": "List items below reorder point.", "input_schema": {"type": "object", "properties": {}}},
        {"name": "check_inventory", "description": "Check inventory for a SKU.", "input_schema": {"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]}},
        {"name": "create_purchase_order", "description": "Create a replenishment PO.", "input_schema": {"type": "object", "properties": {"sku": {"type": "string"}, "quantity": {"type": "integer"}, "supplier": {"type": "string"}}, "required": ["sku", "quantity"]}},
    ]
    _SYSTEM = "You are an async ERP Inventory Agent. Monitor stock and trigger replenishment."

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=self._TOOLS, system_prompt=self._SYSTEM, **kwargs)

    async def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "list_low_stock_items":
                return erp_tools.list_low_stock_items()
            case "check_inventory":
                return erp_tools.check_inventory(**inputs)
            case "create_purchase_order":
                return erp_tools.create_purchase_order(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}


class AsyncMultiAgentOrchestrator:
    """Runs order and inventory agents concurrently via asyncio.gather."""

    def __init__(self, **agent_kwargs) -> None:
        self._order_agent = AsyncOrderAgent(**agent_kwargs)
        self._inventory_agent = AsyncInventoryAgent(**agent_kwargs)

    async def run(self, task: str) -> dict[str, str]:
        """Dispatch to specialist agents in parallel and return all results."""
        task_lower = task.lower()
        words = set(task_lower.split())
        needs_order = bool(words & {"order", "orders", "shipment", "delivery", "customer"})
        needs_inventory = any(kw in task_lower for kw in ("inventory", "stock", "replenish", "reorder", "purchase"))

        if not needs_order and not needs_inventory:
            needs_order = True
            needs_inventory = True

        coros = {}
        if needs_order:
            coros["order_agent"] = self._order_agent.run(task)
        if needs_inventory:
            coros["inventory_agent"] = self._inventory_agent.run(task)

        results = await asyncio.gather(*coros.values())
        return dict(zip(coros.keys(), results))
