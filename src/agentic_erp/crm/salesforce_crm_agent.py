"""Live CRM agent backed by real Salesforce REST API calls."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.connectors.salesforce import SalesforceConfig, SalesforceConnector

_TOOLS = [
    {
        "name": "soql_query",
        "description": "Run a SOQL query against the Salesforce org.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Full SOQL query string (e.g. SELECT Id, Name FROM Lead WHERE Status = 'New' LIMIT 10)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_lead",
        "description": "Retrieve a Salesforce Lead record by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "description": "Salesforce Lead record ID (18-char)"},
            },
            "required": ["record_id"],
        },
    },
    {
        "name": "create_lead",
        "description": "Create a new Salesforce Lead record.",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "Lead field data. Required: LastName, Company.",
                    "properties": {
                        "LastName": {"type": "string"},
                        "Company": {"type": "string"},
                    },
                    "required": ["LastName", "Company"],
                },
            },
            "required": ["data"],
        },
    },
    {
        "name": "update_lead",
        "description": "Update a Salesforce Lead record by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "description": "Salesforce Lead record ID"},
                "data": {"type": "object", "description": "Fields to update on the Lead"},
            },
            "required": ["record_id", "data"],
        },
    },
    {
        "name": "create_opportunity",
        "description": "Create a new Salesforce Opportunity record.",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "Opportunity field data. Required: Name, StageName, CloseDate, AccountId.",
                    "properties": {
                        "Name": {"type": "string"},
                        "StageName": {"type": "string"},
                        "CloseDate": {"type": "string", "description": "ISO date string (YYYY-MM-DD)"},
                        "AccountId": {"type": "string"},
                    },
                    "required": ["Name", "StageName", "CloseDate", "AccountId"],
                },
            },
            "required": ["data"],
        },
    },
    {
        "name": "update_opportunity",
        "description": "Update a Salesforce Opportunity record by ID (e.g. StageName, Amount, Probability).",
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "description": "Salesforce Opportunity record ID"},
                "data": {"type": "object", "description": "Fields to update on the Opportunity"},
            },
            "required": ["record_id", "data"],
        },
    },
    {
        "name": "get_account",
        "description": "Retrieve a Salesforce Account record by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "description": "Salesforce Account record ID (18-char)"},
            },
            "required": ["record_id"],
        },
    },
]

_SYSTEM_PROMPT = (
    "You are a Salesforce CRM Agent with live access to the org. "
    "You manage leads, opportunities, and account data. "
    "Use soql_query for flexible reporting, targeted get/create/update tools for individual records. "
    "Be precise with field names — Salesforce is case-sensitive."
)


class SalesforceCRMAgent(BaseERPAgent):
    """CRM agent wired to a live Salesforce REST API org.

    Usage::

        from agentic_erp.crm.salesforce_crm_agent import SalesforceCRMAgent
        from agentic_erp.connectors.salesforce import SalesforceConfig

        agent = SalesforceCRMAgent(
            config=SalesforceConfig(
                instance_url="https://myorg.my.salesforce.com",
                access_token="00D...",
            )
        )
        result = agent.run("Show me all new leads from this week.")
        print(result)
    """

    def __init__(self, config: SalesforceConfig, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)
        self._sf = SalesforceConnector(config)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "soql_query":
                return self._sf.soql_query(inputs["query"])
            case "get_lead":
                return self._sf.get_record(
                    "Lead",
                    inputs["record_id"],
                    fields=["Id", "FirstName", "LastName", "Company", "Status", "Email"],
                )
            case "create_lead":
                return self._sf.create_record("Lead", inputs["data"])
            case "update_lead":
                return self._sf.update_record("Lead", inputs["record_id"], inputs["data"])
            case "create_opportunity":
                return self._sf.create_record("Opportunity", inputs["data"])
            case "update_opportunity":
                return self._sf.update_record("Opportunity", inputs["record_id"], inputs["data"])
            case "get_account":
                return self._sf.get_record(
                    "Account",
                    inputs["record_id"],
                    fields=["Id", "Name", "Industry", "AnnualRevenue", "BillingCity"],
                )
            case _:
                return {"error": f"Unknown tool: {name}"}
