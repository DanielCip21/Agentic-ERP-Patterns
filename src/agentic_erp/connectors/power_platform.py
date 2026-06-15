"""Live connector for Microsoft Power Platform (Power Automate + Dataverse)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from agentic_erp.connectors.auth import AzureADTokenManager
from agentic_erp.connectors.base import BaseHTTPConnector


class PowerPlatformConfig(BaseModel):
    """Power Platform API configuration."""

    environment_id: str  # e.g. Default-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    environment_url: str  # e.g. https://orgname.crm.dynamics.com  (for Dataverse)
    tenant_id: str
    client_id: str
    client_secret: str
    region: str = "unitedstates"  # used to construct flow API base URL


class _FlowConnector(BaseHTTPConnector):
    """Internal connector for the Power Automate management API."""

    _FLOW_SCOPE = "https://service.flow.microsoft.com/.default"

    def __init__(self, config: PowerPlatformConfig) -> None:
        self._config = config
        self._base_url = (
            f"https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple"
            f"/environments/{config.environment_id}"
        )

    def _auth_headers(self) -> dict[str, str]:
        token = AzureADTokenManager.get_token(
            tenant_id=self._config.tenant_id,
            client_id=self._config.client_id,
            client_secret=self._config.client_secret,
            scope=self._FLOW_SCOPE,
        )
        return {"Authorization": f"Bearer {token}"}


class _DataverseConnector(BaseHTTPConnector):
    """Internal connector for Dataverse operations via Power Platform."""

    def __init__(self, config: PowerPlatformConfig) -> None:
        self._config = config
        self._base_url = f"{config.environment_url}/api/data/v9.2"
        self._scope = f"{config.environment_url}/.default"

    def _auth_headers(self) -> dict[str, str]:
        token = AzureADTokenManager.get_token(
            tenant_id=self._config.tenant_id,
            client_id=self._config.client_id,
            client_secret=self._config.client_secret,
            scope=self._scope,
        )
        return {
            "Authorization": f"Bearer {token}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
        }


class PowerPlatformConnector:
    """Unified client for Power Automate flow management and Dataverse operations.

    Uses two separate internal HTTP connectors because the flow management API
    and Dataverse API require different OAuth2 scopes.

    Usage::

        from agentic_erp.connectors.power_platform import PowerPlatformConfig, PowerPlatformConnector

        conn = PowerPlatformConnector(PowerPlatformConfig(
            environment_id="Default-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            environment_url="https://orgname.crm.dynamics.com",
            tenant_id="...",
            client_id="...",
            client_secret="...",
        ))
        flows = conn.list_flows()
        conn.trigger_flow("flow-id-guid", {"order_id": "ORD-001"})
    """

    def __init__(self, config: PowerPlatformConfig) -> None:
        self.config = config
        self._flow = _FlowConnector(config)
        self._dv = _DataverseConnector(config)

    # --- Power Automate flows -------------------------------------------------

    def list_flows(self, environment_id: str | None = None) -> list[dict[str, Any]]:
        """GET flows — list all flows in the environment."""
        result = self._flow._get("flows", params={"api-version": "2016-11-01"})
        return result.get("value", [])

    def trigger_flow(self, flow_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """POST the manual HTTP trigger on a Power Automate flow."""
        return self._flow._post(
            f"flows/{flow_id}/triggers/manual/run",
            json=body,
        )

    def get_flow_run_status(self, flow_id: str, run_id: str) -> dict[str, Any]:
        """GET the status of a specific flow run."""
        return self._flow._get(
            f"flows/{flow_id}/runs/{run_id}",
            params={"api-version": "2016-11-01"},
        )

    def list_flow_runs(self, flow_id: str, top: int = 20) -> list[dict[str, Any]]:
        """GET recent runs for a flow."""
        result = self._flow._get(
            f"flows/{flow_id}/runs",
            params={"api-version": "2016-11-01", "$top": top},
        )
        return result.get("value", [])

    # --- Dataverse CRUD -------------------------------------------------------

    def create_dataverse_row(self, table: str, data: dict[str, Any]) -> dict[str, Any]:
        """POST /{table} — create a row in a Dataverse table."""
        return self._dv._post(table, json=data)

    def update_dataverse_row(
        self, table: str, row_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """PATCH /{table}({row_id}) — update a Dataverse row."""
        return self._dv._patch(f"{table}({row_id})", json=data)

    def query_dataverse(
        self,
        table: str,
        filter_expr: str = "",
        select_cols: list[str] | None = None,
        top: int = 50,
    ) -> list[dict[str, Any]]:
        """GET /{table} with OData filter + select."""
        params: dict[str, Any] = {"$top": top}
        if filter_expr:
            params["$filter"] = filter_expr
        if select_cols:
            params["$select"] = ",".join(select_cols)
        result = self._dv._get(table, params=params)
        return result.get("value", [])

    def delete_dataverse_row(self, table: str, row_id: str) -> dict[str, Any]:
        """DELETE /{table}({row_id})."""
        return self._dv._delete(f"{table}({row_id})")
