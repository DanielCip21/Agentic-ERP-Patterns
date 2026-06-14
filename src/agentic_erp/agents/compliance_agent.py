"""Pattern: Multi-jurisdiction tax & regulatory compliance automation agent."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import finance_tools

_TOOLS = [
    {
        "name": "get_jurisdiction_rules",
        "description": "Retrieve tax rates, AML thresholds, filing deadlines, and crypto reporting requirements for a country.",
        "input_schema": {
            "type": "object",
            "properties": {
                "country_code": {"type": "string", "description": "ISO 3166-1 alpha-2 country code (e.g. US, EU, SG, JP, AU)"},
            },
            "required": ["country_code"],
        },
    },
    {
        "name": "check_transaction_compliance",
        "description": "Evaluate whether a specific transaction meets AML and tax compliance rules for a jurisdiction.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tx_id": {"type": "string", "description": "Transaction ID to check"},
                "jurisdiction": {"type": "string", "description": "Country code for compliance rules"},
            },
            "required": ["tx_id", "jurisdiction"],
        },
    },
    {
        "name": "generate_compliance_report",
        "description": "Generate a consolidated compliance report covering multiple jurisdictions for a reporting period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "Reporting period (e.g. '2026-Q2', '2026-06')"},
                "jurisdictions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of country codes to include",
                },
            },
            "required": ["period", "jurisdictions"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Global Compliance Automation Agent for a gaming company with operations in
the US, EU, Singapore, Japan, and Australia.
Your responsibilities:
1. Look up jurisdiction-specific VAT rates, withholding taxes, AML thresholds, and filing deadlines.
2. Audit individual transactions for compliance issues in the relevant jurisdiction.
3. Generate consolidated compliance reports for quarterly or annual regulatory filings.
4. Flag any AML threshold breaches, missing crypto disclosures, or overdue filing deadlines.
Be precise about tax amounts. Always cite the specific rule or threshold that applies."""


class ComplianceAgent(BaseERPAgent):
    """Automates multi-jurisdiction tax and regulatory compliance checks."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_jurisdiction_rules":
                return finance_tools.get_jurisdiction_rules(**inputs)
            case "check_transaction_compliance":
                return finance_tools.check_transaction_compliance(**inputs)
            case "generate_compliance_report":
                return finance_tools.generate_compliance_report(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
