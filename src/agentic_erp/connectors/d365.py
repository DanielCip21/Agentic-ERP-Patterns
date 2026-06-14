"""Microsoft Dynamics 365 / Dataverse Web API connector with OAuth 2.0.

Swap the stub functions in ``tools/erp_tools.py`` with methods from this
connector to hit a real Dynamics 365 environment.

Required environment variables:
    D365_TENANT_ID      Azure AD tenant ID
    D365_CLIENT_ID      App registration client ID
    D365_CLIENT_SECRET  App registration client secret
    D365_ENVIRONMENT_URL  e.g. https://yourorg.crm.dynamics.com

Usage:
    from agentic_erp.connectors.d365 import D365Connector

    d365 = D365Connector()
    order = d365.get_record("salesorders", order_id)
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
import urllib.error
from typing import Any


class D365Connector:
    """Thin wrapper around the Dataverse Web API with token caching."""

    _TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    _API_VERSION = "9.2"

    def __init__(
        self,
        tenant_id: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        environment_url: str | None = None,
    ) -> None:
        self._tenant_id = tenant_id or os.environ["D365_TENANT_ID"]
        self._client_id = client_id or os.environ["D365_CLIENT_ID"]
        self._client_secret = client_secret or os.environ["D365_CLIENT_SECRET"]
        self._env_url = (environment_url or os.environ["D365_ENVIRONMENT_URL"]).rstrip("/")

        self._access_token: str | None = None
        self._token_expiry: float = 0.0

    # ------------------------------------------------------------------
    # Public CRUD helpers
    # ------------------------------------------------------------------

    def get_record(self, entity: str, record_id: str, select: list[str] | None = None) -> dict[str, Any]:
        """GET /api/data/v{ver}/{entity}({record_id})"""
        params = f"?$select={','.join(select)}" if select else ""
        return self._request("GET", f"{entity}({record_id}){params}")

    def list_records(
        self,
        entity: str,
        filter_: str | None = None,
        select: list[str] | None = None,
        top: int | None = None,
    ) -> list[dict[str, Any]]:
        """GET /api/data/v{ver}/{entity} with optional $filter, $select, $top."""
        parts = []
        if filter_:
            parts.append(f"$filter={urllib.parse.quote(filter_)}")
        if select:
            parts.append(f"$select={','.join(select)}")
        if top:
            parts.append(f"$top={top}")
        qs = ("?" + "&".join(parts)) if parts else ""
        result = self._request("GET", f"{entity}{qs}")
        return result.get("value", [])

    def create_record(self, entity: str, data: dict[str, Any]) -> dict[str, Any]:
        """POST /api/data/v{ver}/{entity}"""
        return self._request("POST", entity, body=data)

    def update_record(self, entity: str, record_id: str, data: dict[str, Any]) -> None:
        """PATCH /api/data/v{ver}/{entity}({record_id})"""
        self._request("PATCH", f"{entity}({record_id})", body=data)

    def delete_record(self, entity: str, record_id: str) -> None:
        """DELETE /api/data/v{ver}/{entity}({record_id})"""
        self._request("DELETE", f"{entity}({record_id})")

    # ------------------------------------------------------------------
    # Convenience wrappers matching erp_tools.py signatures
    # ------------------------------------------------------------------

    def get_order(self, order_id: str) -> dict[str, Any]:
        return self.get_record("salesorders", order_id)

    def update_order_status(self, order_id: str, status: str) -> dict[str, Any]:
        self.update_record("salesorders", order_id, {"statuscode": status})
        return {"order_id": order_id, "status": status}

    def check_inventory(self, sku: str) -> dict[str, Any]:
        records = self.list_records("products", filter_=f"productnumber eq '{sku}'", top=1)
        return records[0] if records else {"error": f"SKU {sku} not found"}

    def create_purchase_order(self, sku: str, quantity: int, supplier: str = "") -> dict[str, Any]:
        return self.create_record("purchaseorders", {"sku": sku, "quantity": quantity, "supplier": supplier})

    # ------------------------------------------------------------------
    # Auth & HTTP
    # ------------------------------------------------------------------

    def _get_token(self) -> str:
        if self._access_token and time.monotonic() < self._token_expiry:
            return self._access_token

        url = self._TOKEN_URL.format(tenant_id=self._tenant_id)
        body = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": f"{self._env_url}/.default",
        }).encode()

        req = urllib.request.Request(url, data=body, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            token_data = json.loads(resp.read())

        self._access_token = token_data["access_token"]
        self._token_expiry = time.monotonic() + token_data.get("expires_in", 3600) - 60
        return self._access_token

    def _request(self, method: str, path: str, body: dict | None = None) -> Any:
        url = f"{self._env_url}/api/data/v{self._API_VERSION}/{path}"
        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "Accept": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
        }
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"D365 API error {exc.code}: {exc.read().decode()}") from exc
