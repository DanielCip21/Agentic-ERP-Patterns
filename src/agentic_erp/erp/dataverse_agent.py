"""Live ERP agent backed by real Microsoft Dataverse Web API calls."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.connectors.dataverse import DataverseConfig, DataverseConnector

_TOOLS = [
    {
        "name": "query_table",
        "description": "OData query on any Dataverse table with optional filtering and column selection.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Dataverse table (plural) name, e.g. accounts"},
                "filter_expr": {"type": "string", "description": "OData $filter expression"},
                "select_cols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns to include in the response",
                },
                "order_by": {"type": "string", "description": "OData $orderby expression"},
                "top": {"type": "integer", "description": "Max records to return (default 50)"},
                "expand": {"type": "string", "description": "OData $expand expression for related entities"},
            },
            "required": ["table"],
        },
    },
    {
        "name": "get_record",
        "description": "Get a single Dataverse record by its primary key GUID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Dataverse table (plural) name"},
                "record_id": {"type": "string", "description": "Primary key GUID of the record"},
                "select_cols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns to include in the response",
                },
            },
            "required": ["table", "record_id"],
        },
    },
    {
        "name": "create_record",
        "description": "Create a new record in a Dataverse table.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Dataverse table (plural) name"},
                "data": {"type": "object", "description": "Field values for the new record"},
            },
            "required": ["table", "data"],
        },
    },
    {
        "name": "update_record",
        "description": "Patch (partial update) an existing Dataverse record by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Dataverse table (plural) name"},
                "record_id": {"type": "string", "description": "Primary key GUID of the record to update"},
                "data": {"type": "object", "description": "Fields to update on the record"},
            },
            "required": ["table", "record_id", "data"],
        },
    },
    {
        "name": "upsert_record",
        "description": "Upsert a Dataverse record using an alternate key.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Dataverse table (plural) name"},
                "alternate_key": {"type": "string", "description": "Alternate key field name"},
                "key_value": {"type": "string", "description": "Value of the alternate key"},
                "data": {"type": "object", "description": "Field values to set on the record"},
            },
            "required": ["table", "alternate_key", "key_value", "data"],
        },
    },
    {
        "name": "delete_record",
        "description": "Delete a Dataverse record by its primary key GUID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Dataverse table (plural) name"},
                "record_id": {"type": "string", "description": "Primary key GUID of the record to delete"},
            },
            "required": ["table", "record_id"],
        },
    },
    {
        "name": "associate_records",
        "description": "Create a N:N association between two Dataverse records via a relationship.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Primary table (plural) name"},
                "record_id": {"type": "string", "description": "Primary key GUID of the primary record"},
                "relationship": {"type": "string", "description": "Relationship name (e.g. account_contacts)"},
                "related_table": {"type": "string", "description": "Related table (plural) name"},
                "related_id": {"type": "string", "description": "Primary key GUID of the related record"},
            },
            "required": ["table", "record_id", "relationship", "related_table", "related_id"],
        },
    },
    {
        "name": "execute_fetch_xml",
        "description": "Run a FetchXML query for complex multi-entity reports not expressible in OData.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Root entity (plural) table name"},
                "fetch_xml": {"type": "string", "description": "FetchXML query string"},
            },
            "required": ["table", "fetch_xml"],
        },
    },
]

_SYSTEM_PROMPT = (
    "You are a Microsoft Dataverse Agent with direct access to the Dataverse Web API (OData v4). "
    "You can query any table with filters and column selection, create and update records, manage N:N "
    "relationships, and run FetchXML for complex cross-entity reports. Use query_table for filtered list "
    "queries, get_record for a single record by GUID, and execute_fetch_xml for joins or aggregates not "
    "expressible in OData."
)


class DataverseAgent(BaseERPAgent):
    """Dataverse agent wired to the live Dataverse Web API.

    Usage::

        from agentic_erp.erp.dataverse_agent import DataverseAgent
        from agentic_erp.connectors.dataverse import DataverseConfig

        agent = DataverseAgent(
            config=DataverseConfig(
                environment_url="https://myorg.crm.dynamics.com",
                tenant_id="your-tenant-id",
                client_id="your-app-registration-client-id",
                client_secret="your-client-secret",
            )
        )
        result = agent.run("List all active accounts with their revenue.")
        print(result)
    """

    def __init__(self, config: DataverseConfig, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)
        self._dv = DataverseConnector(config)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "query_table":
                return self._dv.query(
                    inputs["table"],
                    filter_expr=inputs.get("filter_expr", ""),
                    select_cols=inputs.get("select_cols", None),
                    order_by=inputs.get("order_by", ""),
                    top=inputs.get("top", 50),
                    expand=inputs.get("expand", ""),
                )
            case "get_record":
                return self._dv.get(
                    inputs["table"],
                    inputs["record_id"],
                    select_cols=inputs.get("select_cols", None),
                )
            case "create_record":
                return self._dv.create(inputs["table"], inputs["data"])
            case "update_record":
                return self._dv.update(inputs["table"], inputs["record_id"], inputs["data"])
            case "upsert_record":
                return self._dv.upsert(
                    inputs["table"],
                    inputs["alternate_key"],
                    inputs["key_value"],
                    inputs["data"],
                )
            case "delete_record":
                return self._dv.delete(inputs["table"], inputs["record_id"])
            case "associate_records":
                return self._dv.associate(
                    inputs["table"],
                    inputs["record_id"],
                    inputs["relationship"],
                    inputs["related_table"],
                    inputs["related_id"],
                )
            case "execute_fetch_xml":
                return self._dv.execute_fetch_xml(inputs["table"], inputs["fetch_xml"])
            case _:
                return {"error": f"Unknown tool: {name}"}
