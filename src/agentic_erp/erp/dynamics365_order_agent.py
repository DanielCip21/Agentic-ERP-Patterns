"""Live ERP order agent backed by real Dynamics 365 API calls."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.connectors.dynamics365 import Dynamics365Config, Dynamics365Connector

_TOOLS = [
    {
        "name": "get_order",
        "description": "Retrieve a Dynamics 365 sales order by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Dynamics 365 salesorderid (GUID)"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "list_orders",
        "description": "List sales orders, optionally filtered by an OData expression.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter_expr": {"type": "string", "description": "OData $filter expression (e.g. statecode eq 0)"},
                "top": {"type": "integer", "description": "Max records to return (default 50)"},
            },
        },
    },
    {
        "name": "update_order_status",
        "description": "Update the status code of a Dynamics 365 sales order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "state_code": {"type": "integer", "description": "0=Active, 1=Submitted, 2=Cancelled, 3=Fulfilled, 4=Invoiced"},
                "status_code": {"type": "integer", "description": "Substatus code matching the state"},
            },
            "required": ["order_id", "state_code", "status_code"],
        },
    },
    {
        "name": "get_account",
        "description": "Retrieve a Dynamics 365 account record for a customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "Dynamics 365 accountid (GUID)"},
            },
            "required": ["account_id"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Dynamics 365 Order Processing Agent with live access to the CRM.
Retrieve order details, verify customer accounts, and update order status codes as needed.
Always confirm the current statecode before updating. Be concise and factual."""


class Dynamics365OrderAgent(BaseERPAgent):
    """Order processing agent wired to live Dynamics 365 Web API.

    Usage::

        from agentic_erp.erp.dynamics365_order_agent import Dynamics365OrderAgent
        from agentic_erp.connectors.dynamics365 import Dynamics365Config

        agent = Dynamics365OrderAgent(
            config=Dynamics365Config(
                tenant_id="your-tenant-id",
                client_id="your-app-registration-client-id",
                client_secret="your-client-secret",
                environment_url="https://yourorg.crm.dynamics.com",
            )
        )
        result = agent.run("List all active sales orders and summarise their status.")
        print(result)
    """

    def __init__(self, config: Dynamics365Config, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)
        self._d365 = Dynamics365Connector(config)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_order":
                return self._d365.get_sales_order(inputs["order_id"])
            case "list_orders":
                return self._d365.get_sales_orders(
                    filter_expr=inputs.get("filter_expr", ""),
                    top=inputs.get("top", 50),
                )
            case "update_order_status":
                return self._d365.update_sales_order(
                    inputs["order_id"],
                    {"statecode": inputs["state_code"], "statuscode": inputs["status_code"]},
                )
            case "get_account":
                return self._d365.get_account(inputs["account_id"])
            case _:
                return {"error": f"Unknown tool: {name}"}
