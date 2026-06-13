"""Pattern: AI-powered Accounts Payable & Vendor Management agent."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import ap_tools

_TOOLS = [
    {
        "name": "detect_duplicate_invoices",
        "description": "Scan all pending invoices for duplicates using AI pattern matching.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "three_way_match",
        "description": "Perform three-way matching (invoice vs PO vs receipt) for a given invoice.",
        "input_schema": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string", "description": "Invoice ID to verify (e.g. INV-001)"},
            },
            "required": ["invoice_id"],
        },
    },
    {
        "name": "score_vendor",
        "description": "Generate an AI-driven composite score for a vendor based on credit and on-time delivery.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vendor_id": {"type": "string", "description": "Vendor ID (e.g. VND-001)"},
            },
            "required": ["vendor_id"],
        },
    },
    {
        "name": "list_invoices_due",
        "description": "List all invoices due within a specified number of days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {"type": "integer", "description": "Days ahead to look (default 30)"},
            },
        },
    },
    {
        "name": "approve_invoice",
        "description": "Approve an invoice for payment after validation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string"},
            },
            "required": ["invoice_id"],
        },
    },
    {
        "name": "calculate_dynamic_discount",
        "description": "Calculate early payment discount savings for an invoice.",
        "input_schema": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string"},
                "pay_in_days": {"type": "integer", "description": "Number of days in which payment will be made"},
            },
            "required": ["invoice_id", "pay_in_days"],
        },
    },
]

_SYSTEM_PROMPT = """You are an AI-powered Accounts Payable Agent.
Your responsibilities:
- Detect duplicate invoices before they are paid
- Perform three-way matching (invoice / PO / goods receipt) and flag discrepancies
- Score vendors by performance and flag high-risk suppliers
- Identify upcoming invoice due dates and prioritize payments
- Calculate early payment discounts to optimize working capital
Always recommend whether to approve, hold, or escalate each invoice."""


class APAutomationAgent(BaseERPAgent):
    """AI-driven AP processing: duplicate detection, 3-way match, vendor scoring."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "detect_duplicate_invoices":
                return ap_tools.detect_duplicate_invoices()
            case "three_way_match":
                return ap_tools.three_way_match(**inputs)
            case "score_vendor":
                return ap_tools.score_vendor(**inputs)
            case "list_invoices_due":
                return ap_tools.list_invoices_due(**inputs)
            case "approve_invoice":
                return ap_tools.approve_invoice(**inputs)
            case "calculate_dynamic_discount":
                return ap_tools.calculate_dynamic_discount(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
