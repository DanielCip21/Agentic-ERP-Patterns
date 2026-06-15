"""Pattern: Tool-use agent for procurement — vendor RFQ, PO creation, 3-way match."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.erp import procurement_tools

_TOOLS = [
    {
        "name": "search_vendors",
        "description": "Search approved vendors by category and minimum rating.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Vendor category (e.g. raw_materials, electronics, packaging)",
                },
                "min_rating": {
                    "type": "number",
                    "description": "Minimum vendor rating (0-5). Default 0.",
                },
            },
            "required": ["category"],
        },
    },
    {
        "name": "create_rfq",
        "description": "Send a Request for Quotation to a list of vendors for specified items.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vendor_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of vendor IDs to send RFQ",
                },
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "sku": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "description": {"type": "string"},
                        },
                        "required": ["sku", "quantity"],
                    },
                    "description": "Items to request quotes for",
                },
            },
            "required": ["vendor_ids", "items"],
        },
    },
    {
        "name": "create_purchase_order",
        "description": "Create an approved purchase order with a vendor.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vendor_id": {"type": "string", "description": "Vendor ID"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "sku": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "unit_price": {"type": "number"},
                        },
                        "required": ["sku", "quantity", "unit_price"],
                    },
                    "description": "Line items for the PO",
                },
                "total": {"type": "number", "description": "Total PO value in USD"},
            },
            "required": ["vendor_id", "items", "total"],
        },
    },
    {
        "name": "match_invoice_to_po",
        "description": "Perform 3-way match: compare invoice amount against purchase order total to detect discrepancies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string", "description": "Invoice ID"},
                "po_id": {"type": "string", "description": "Purchase Order ID"},
            },
            "required": ["invoice_id", "po_id"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Procurement Automation Agent for an enterprise ERP system.
Your responsibilities:
1. Source qualified vendors by category and rating criteria
2. Issue Requests for Quotation (RFQ) to shortlisted vendors
3. Create purchase orders once a vendor is selected
4. Perform 3-way matching (PO / goods receipt / invoice) to detect billing discrepancies

Always verify vendor ratings before issuing RFQs. Flag any invoice variance above $50 for manual review.
Be precise with financial figures and procurement timelines."""


class ProcurementAgent(BaseERPAgent):
    """Automates vendor sourcing, RFQ issuance, PO creation, and 3-way invoice matching."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "search_vendors":
                return procurement_tools.search_vendors(**inputs)
            case "create_rfq":
                return procurement_tools.create_rfq(**inputs)
            case "create_purchase_order":
                return procurement_tools.create_purchase_order(**inputs)
            case "match_invoice_to_po":
                return procurement_tools.match_invoice_to_po(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
