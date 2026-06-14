"""Pattern: AI-powered Supply Chain & Procurement optimization agent."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import supply_chain_tools

_TOOLS = [
    {
        "name": "select_optimal_supplier",
        "description": "AI-driven supplier selection scoring cost, reliability, and lead time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {"type": "string", "description": "Product SKU to source"},
                "quantity": {"type": "integer", "description": "Quantity required"},
                "priority": {"type": "string", "enum": ["cost", "speed", "balanced"], "description": "Optimization priority (default: balanced)"},
            },
            "required": ["sku", "quantity"],
        },
    },
    {
        "name": "forecast_demand",
        "description": "AI-based demand forecasting using historical sales data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {"type": "string", "description": "Product SKU to forecast"},
                "months_ahead": {"type": "integer", "description": "Months to forecast ahead (default 3)"},
            },
            "required": ["sku"],
        },
    },
    {
        "name": "track_shipment",
        "description": "Get real-time IoT-based shipment tracking status and delay risk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "shipment_id": {"type": "string", "description": "Shipment ID (e.g. SHIP-001)"},
            },
            "required": ["shipment_id"],
        },
    },
    {
        "name": "assess_supply_chain_risk",
        "description": "Assess geopolitical, reliability, and lead time risks for a supplier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "supplier_id": {"type": "string", "description": "Supplier ID (e.g. SUP-001)"},
            },
            "required": ["supplier_id"],
        },
    },
    {
        "name": "optimize_freight_cost",
        "description": "Compare freight carriers and recommend the lowest-cost option.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string"},
                "destination": {"type": "string"},
                "weight_kg": {"type": "number", "description": "Shipment weight in kilograms"},
            },
            "required": ["origin", "destination", "weight_kg"],
        },
    },
]

_SYSTEM_PROMPT = """You are an AI-powered Supply Chain & Procurement Agent.
Your responsibilities:
- Select the optimal supplier for each SKU based on cost, reliability, and speed
- Forecast future demand using AI/ML models to prevent stockouts and overstock
- Track shipments in real time and flag delay risks proactively
- Assess geopolitical and operational risks for key suppliers
- Optimize freight costs by selecting the best carrier for each shipment
Always consider total landed cost, not just unit price, when recommending suppliers."""


class SupplyChainAgent(BaseERPAgent):
    """AI-driven supply chain: supplier selection, demand forecasting, risk assessment."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "select_optimal_supplier":
                return supply_chain_tools.select_optimal_supplier(**inputs)
            case "forecast_demand":
                return supply_chain_tools.forecast_demand(**inputs)
            case "track_shipment":
                return supply_chain_tools.track_shipment(**inputs)
            case "assess_supply_chain_risk":
                return supply_chain_tools.assess_supply_chain_risk(**inputs)
            case "optimize_freight_cost":
                return supply_chain_tools.optimize_freight_cost(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
