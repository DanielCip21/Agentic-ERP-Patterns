"""Live connector for Microsoft Dataverse Web API (OData v4)."""

from __future__ import annotations

import urllib.parse
from typing import Any

from pydantic import BaseModel

from agentic_erp.connectors.auth import AzureADTokenManager
from agentic_erp.connectors.base import BaseHTTPConnector


class DataverseConfig(BaseModel):
    """Dataverse Web API configuration."""

    environment_url: str   # e.g. https://orgname.api.crm.dynamics.com
    tenant_id: str
    client_id: str
    client_secret: str
    api_version: str = "v9.2"


class DataverseConnector(BaseHTTPConnector):
    """Live client for the Microsoft Dataverse Web API (OData v4).

    Authentication: Azure AD client_credentials grant.
    Scope is derived automatically from the environment_url.

    Usage::

        from agentic_erp.connectors.dataverse import DataverseConfig, DataverseConnector

        conn = DataverseConnector(DataverseConfig(
            environment_url="https://orgname.api.crm.dynamics.com",
            tenant_id="...",
            client_id="...",
            client_secret="...",
        ))

        accounts = conn.query("accounts", filter_expr="statecode eq 0",
                              select_cols=["accountid", "name", "revenue"])
        new_lead = conn.create("leads", {"lastname": "Smith", "companyname": "Acme"})
    """

    def __init__(self, config: DataverseConfig) -> None:
        self.config = config
        self._base_url = f"{config.environment_url}/api/data/{config.api_version}"
        self._scope = f"{config.environment_url}/.default"

    def _auth_headers(self) -> dict[str, str]:
        token = AzureADTokenManager.get_token(
            tenant_id=self.config.tenant_id,
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            scope=self._scope,
        )
        return {
            "Authorization": f"Bearer {token}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Prefer": "odata.include-annotations=OData.Community.Display.V1.FormattedValue",
        }

    # --- Query ----------------------------------------------------------------

    def query(
        self,
        table: str,
        filter_expr: str = "",
        select_cols: list[str] | None = None,
        order_by: str = "",
        top: int = 50,
        expand: str = "",
    ) -> dict[str, Any]:
        """GET /{table} with OData $filter, $select, $orderby, $top, $expand."""
        params: dict[str, Any] = {"$top": top}
        if filter_expr:
            params["$filter"] = filter_expr
        if select_cols:
            params["$select"] = ",".join(select_cols)
        if order_by:
            params["$orderby"] = order_by
        if expand:
            params["$expand"] = expand
        return self._get(table, params=params)

    def get(self, table: str, record_id: str, select_cols: list[str] | None = None) -> dict[str, Any]:
        """GET /{table}({record_id}) — single record by primary key."""
        params = {"$select": ",".join(select_cols)} if select_cols else None
        return self._get(f"{table}({record_id})", params=params)

    # --- Write ----------------------------------------------------------------

    def create(self, table: str, data: dict[str, Any]) -> dict[str, Any]:
        """POST /{table} — returns 201 with the created record (Prefer: return=representation)."""
        return self._post(table, json=data)

    def update(self, table: str, record_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """PATCH /{table}({record_id}) — returns 204 No Content."""
        return self._patch(f"{table}({record_id})", json=data)

    def upsert(self, table: str, alternate_key: str, key_value: str, data: dict[str, Any]) -> dict[str, Any]:
        """PATCH /{table}({alternateKey}='{keyValue}') — upsert by alternate key."""
        return self._patch(f"{table}({alternate_key}='{key_value}')", json=data)

    def delete(self, table: str, record_id: str) -> dict[str, Any]:
        """DELETE /{table}({record_id}) — returns 204 No Content."""
        return self._delete(f"{table}({record_id})")

    # --- Relationships --------------------------------------------------------

    def associate(
        self, table: str, record_id: str, relationship: str, related_table: str, related_id: str
    ) -> dict[str, Any]:
        """POST /{table}({id})/{relationship}/$ref — create a N:N association."""
        return self._post(
            f"{table}({record_id})/{relationship}/$ref",
            json={"@odata.id": f"{self._base_url}/{related_table}({related_id})"},
        )

    def disassociate(self, table: str, record_id: str, relationship: str, related_id: str) -> dict[str, Any]:
        """DELETE /{table}({id})/{relationship}({related_id})/$ref — remove N:N link."""
        return self._delete(f"{table}({record_id})/{relationship}({related_id})/$ref")

    # --- Batch / FetchXML -----------------------------------------------------

    def execute_fetch_xml(self, table: str, fetch_xml: str) -> list[dict[str, Any]]:
        """GET /{table}?fetchXml={encoded} — complex multi-entity FetchXML query."""
        encoded = urllib.parse.quote(fetch_xml)
        result = self._get(f"{table}?fetchXml={encoded}")
        return result.get("value", [])

    def batch(self, requests: list[dict[str, Any]]) -> dict[str, Any]:
        """POST /$batch — execute multiple operations in a single round trip."""
        return self._post("$batch", json={"requests": requests})
