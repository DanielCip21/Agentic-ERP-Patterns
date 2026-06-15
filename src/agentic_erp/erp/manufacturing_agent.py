"""Pattern: Tool-use agent for manufacturing — production scheduling, BOM, work orders, capacity."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.erp import manufacturing_tools

_TOOLS = [
    {
        "name": "get_production_schedule",
        "description": "Retrieve the current production schedule showing all planned and in-progress work.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "explode_bom",
        "description": "Explode the Bill of Materials for a product to determine component requirements for a given production quantity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Product ID (e.g. PROD-001)",
                },
                "quantity": {
                    "type": "integer",
                    "description": "Production quantity to plan for",
                },
            },
            "required": ["product_id", "quantity"],
        },
    },
    {
        "name": "create_work_order",
        "description": "Create and release a work order for production.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Product ID to manufacture",
                },
                "quantity": {"type": "integer", "description": "Quantity to produce"},
                "due_date": {
                    "type": "string",
                    "description": "Required completion date in YYYY-MM-DD format",
                },
            },
            "required": ["product_id", "quantity", "due_date"],
        },
    },
    {
        "name": "check_capacity",
        "description": "Check available capacity at a specific workcenter on a given date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workcenter_id": {
                    "type": "string",
                    "description": "Workcenter ID (e.g. WC-001)",
                },
                "date": {
                    "type": "string",
                    "description": "Date to check in YYYY-MM-DD format",
                },
            },
            "required": ["workcenter_id", "date"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Manufacturing Planning Agent for an enterprise ERP system.
Your responsibilities:
1. Review the production schedule to understand current and upcoming workloads
2. Explode Bills of Materials to identify component requirements and procurement lead times
3. Create and release work orders to manufacturing workcenters
4. Verify workcenter capacity before scheduling production to prevent overloading

Always check capacity before creating work orders. Alert planners when components have lead times
that may jeopardize due dates. Optimize production sequences to maximize throughput."""


class ManufacturingAgent(BaseERPAgent):
    """Manages production scheduling, BOM explosion, work order creation, and capacity planning."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_production_schedule":
                return manufacturing_tools.get_production_schedule()
            case "explode_bom":
                return manufacturing_tools.explode_bom(**inputs)
            case "create_work_order":
                return manufacturing_tools.create_work_order(**inputs)
            case "check_capacity":
                return manufacturing_tools.check_capacity(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
