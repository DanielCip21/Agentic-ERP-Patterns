"""Live connector for Microsoft Dynamics 365 Web API (OData v4)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from agentic_erp.connectors.auth import AzureADTokenManager
from agentic_erp.connectors.base import BaseHTTPConnector


class Dynamics365Config(BaseModel):
    tenant_id: str
    client_id: str
    client_secret: str
    environment_url: str  # e.g. https://orgname.crm.dynamics.com
    api_version: str = "v9.2"


class Dynamics365Connector(BaseHTTPConnector):
    """Live client for the Dynamics 365 Web API.

    Authentication: Azure AD client_credentials grant.
    Tokens are cached and refreshed automatically by AzureADTokenManager.

    Usage::

        from agentic_erp.connectors.dynamics365 import Dynamics365Config, Dynamics365Connector

        connector = Dynamics365Connector(Dynamics365Config(
            tenant_id="...",
            client_id="...",
            client_secret="...",
            environment_url="https://myorg.crm.dynamics.com",
        ))
        account = connector.get_account("00000000-0000-0000-0000-000000000001")
    """

    def __init__(self, config: Dynamics365Config) -> None:
        self.config = config
        self._base_url = f"{config.environment_url}/api/data/{config.api_version}"
        # OData scope is always environment_url/.default
        self._scope = f"{config.environment_url}/.default"

    # --- Auth ------------------------------------------------------------------

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

    # --- Accounts --------------------------------------------------------------

    def get_account(
        self, account_id: str, select: list[str] | None = None
    ) -> dict[str, Any]:
        """GET /accounts({account_id})"""
        params = {"$select": ",".join(select)} if select else None
        return self._get(f"accounts({account_id})", params=params)

    def list_accounts(
        self, filter_expr: str = "", select: list[str] | None = None, top: int = 50
    ) -> list[dict[str, Any]]:
        """GET /accounts with optional OData $filter, $select, $top."""
        params: dict[str, Any] = {"$top": top}
        if filter_expr:
            params["$filter"] = filter_expr
        if select:
            params["$select"] = ",".join(select)
        result = self._get("accounts", params=params)
        return result.get("value", [])

    # --- Leads -----------------------------------------------------------------

    def create_lead(self, data: dict[str, Any]) -> dict[str, Any]:
        """POST /leads — returns the created lead with its new leadid."""
        return self._post("leads", json=data)

    def get_lead(self, lead_id: str) -> dict[str, Any]:
        return self._get(f"leads({lead_id})")

    # --- Opportunities ---------------------------------------------------------

    def get_opportunity(self, opp_id: str) -> dict[str, Any]:
        return self._get(f"opportunities({opp_id})")

    def update_opportunity(self, opp_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """PATCH /opportunities({opp_id}) — returns 204 No Content on success."""
        return self._patch(f"opportunities({opp_id})", json=data)

    def list_opportunities(
        self, filter_expr: str = "", select: list[str] | None = None, top: int = 50
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"$top": top}
        if filter_expr:
            params["$filter"] = filter_expr
        if select:
            params["$select"] = ",".join(select)
        result = self._get("opportunities", params=params)
        return result.get("value", [])

    # --- Sales Orders ----------------------------------------------------------

    def get_sales_order(self, order_id: str) -> dict[str, Any]:
        return self._get(f"salesorders({order_id})")

    def get_sales_orders(
        self, filter_expr: str = "", top: int = 50
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"$top": top}
        if filter_expr:
            params["$filter"] = filter_expr
        result = self._get("salesorders", params=params)
        return result.get("value", [])

    def update_sales_order(self, order_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return self._patch(f"salesorders({order_id})", json=data)

    # --- Contacts --------------------------------------------------------------

    def create_contact(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._post("contacts", json=data)

    def get_contact(self, contact_id: str) -> dict[str, Any]:
        return self._get(f"contacts({contact_id})")

    # --- Generic OData ---------------------------------------------------------

    def execute_fetch_xml(self, entity: str, fetch_xml: str) -> list[dict[str, Any]]:
        """POST /entity?fetchXml=... for complex multi-entity queries."""
        import urllib.parse

        encoded = urllib.parse.quote(fetch_xml)
        result = self._get(f"{entity}?fetchXml={encoded}")
        return result.get("value", [])
