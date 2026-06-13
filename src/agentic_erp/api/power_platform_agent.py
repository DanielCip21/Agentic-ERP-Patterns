"""Live Power Platform agent backed by real Power Automate and Dataverse API calls."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.connectors.power_platform import PowerPlatformConfig, PowerPlatformConnector

_TOOLS = [
    {
        "name": "list_flows",
        "description": "List all Power Automate flows in the environment.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "trigger_flow",
        "description": "Trigger a Power Automate flow by ID with a JSON payload.",
        "input_schema": {
            "type": "object",
            "properties": {
                "flow_id": {"type": "string", "description": "The GUID of the Power Automate flow to trigger"},
                "payload": {
                    "type": "object",
                    "description": "JSON body to send as the flow trigger input",
                    "additionalProperties": True,
                },
            },
            "required": ["flow_id", "payload"],
        },
    },
    {
        "name": "get_flow_run_status",
        "description": "Check the status of a specific Power Automate flow run.",
        "input_schema": {
            "type": "object",
            "properties": {
                "flow_id": {"type": "string", "description": "The GUID of the Power Automate flow"},
                "run_id": {"type": "string", "description": "The run ID returned when the flow was triggered"},
            },
            "required": ["flow_id", "run_id"],
        },
    },
    {
        "name": "list_flow_runs",
        "description": "List recent runs for a Power Automate flow.",
        "input_schema": {
            "type": "object",
            "properties": {
                "flow_id": {"type": "string", "description": "The GUID of the Power Automate flow"},
                "top": {"type": "integer", "description": "Maximum number of runs to return (default 20)"},
            },
            "required": ["flow_id"],
        },
    },
    {
        "name": "query_dataverse",
        "description": "Query a Dataverse table using OData filter expressions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Dataverse table (entity set) name"},
                "filter_expr": {"type": "string", "description": "OData $filter expression (e.g. statecode eq 0)"},
                "select_cols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of column names to return ($select)",
                },
                "top": {"type": "integer", "description": "Maximum number of rows to return"},
            },
            "required": ["table"],
        },
    },
    {
        "name": "create_dataverse_row",
        "description": "Create a new record in a Dataverse table.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Dataverse table (entity set) name"},
                "data": {
                    "type": "object",
                    "description": "Field values for the new record",
                    "additionalProperties": True,
                },
            },
            "required": ["table", "data"],
        },
    },
    {
        "name": "update_dataverse_row",
        "description": "Update an existing record in a Dataverse table.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Dataverse table (entity set) name"},
                "row_id": {"type": "string", "description": "GUID of the row to update"},
                "data": {
                    "type": "object",
                    "description": "Fields to update on the record",
                    "additionalProperties": True,
                },
            },
            "required": ["table", "row_id", "data"],
        },
    },
]

_SYSTEM_PROMPT = (
    "You are a Power Platform Automation Agent. "
    "Use Power Automate flow tools to trigger, monitor, and manage business process flows. "
    "Use Dataverse tools to query and update business data. "
    "Always check flow run status after triggering to confirm success."
)


class PowerPlatformAgent(BaseERPAgent):
    """Power Platform automation agent wired to live Power Automate and Dataverse APIs.

    Usage::

        from agentic_erp.api.power_platform_agent import PowerPlatformAgent
        from agentic_erp.connectors.power_platform import PowerPlatformConfig

        agent = PowerPlatformAgent(
            config=PowerPlatformConfig(
                environment_id="Default-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                environment_url="https://yourorg.crm.dynamics.com",
                tenant_id="your-tenant-id",
                client_id="your-app-registration-client-id",
                client_secret="your-client-secret",
            )
        )
        result = agent.run("List all active flows and trigger the order-approval flow.")
        print(result)
    """

    def __init__(self, config: PowerPlatformConfig, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)
        self._pp = PowerPlatformConnector(config)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "list_flows":
                return self._pp.list_flows()
            case "trigger_flow":
                return self._pp.trigger_flow(inputs["flow_id"], body=inputs["payload"])
            case "get_flow_run_status":
                return self._pp.get_flow_run_status(inputs["flow_id"], inputs["run_id"])
            case "list_flow_runs":
                return self._pp.list_flow_runs(
                    inputs["flow_id"],
                    top=inputs.get("top", 20),
                )
            case "query_dataverse":
                return self._pp.query_dataverse(
                    inputs["table"],
                    filter_expr=inputs.get("filter_expr", ""),
                    select_cols=inputs.get("select_cols"),
                    top=inputs.get("top", 50),
                )
            case "create_dataverse_row":
                return self._pp.create_dataverse_row(inputs["table"], inputs["data"])
            case "update_dataverse_row":
                return self._pp.update_dataverse_row(inputs["table"], inputs["row_id"], inputs["data"])
            case _:
                return {"error": f"Unknown tool: {name}"}
