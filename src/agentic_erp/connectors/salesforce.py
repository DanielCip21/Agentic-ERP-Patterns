"""Live connector for Salesforce REST API (SOQL + sObject CRUD)."""

from __future__ import annotations

import urllib.parse
from typing import Any

from pydantic import BaseModel, model_validator

from agentic_erp.connectors.auth import SalesforceTokenManager
from agentic_erp.connectors.base import BaseHTTPConnector


class SalesforceConfig(BaseModel):
    """Salesforce REST API configuration.

    Auth options (provide one):
      - ``access_token``: pre-fetched bearer token (CLI / JWT / session)
      - ``client_id`` + ``client_secret``: Connected App OAuth2 client_credentials flow
    """

    instance_url: str            # e.g. https://myorg.my.salesforce.com
    api_version: str = "v60.0"
    login_url: str = "https://login.salesforce.com"

    # Option A — pre-fetched token
    access_token: str | None = None

    # Option B — Connected App OAuth2
    client_id: str | None = None
    client_secret: str | None = None

    @model_validator(mode="after")
    def _require_auth(self) -> "SalesforceConfig":
        has_token = bool(self.access_token)
        has_oauth = bool(self.client_id and self.client_secret)
        if not has_token and not has_oauth:
            raise ValueError(
                "Provide either access_token OR both client_id and client_secret."
            )
        return self


class SalesforceConnector(BaseHTTPConnector):
    """Live client for the Salesforce REST API.

    Authentication:
      - Pre-fetched access_token (simplest, for scripts / short-lived sessions)
      - OAuth2 client_credentials via Connected App (recommended for daemons)

    Usage::

        from agentic_erp.connectors.salesforce import SalesforceConfig, SalesforceConnector

        # Option A — token you already have
        conn = SalesforceConnector(SalesforceConfig(
            instance_url="https://myorg.my.salesforce.com",
            access_token="00D...",
        ))

        # Option B — Connected App (token managed automatically)
        conn = SalesforceConnector(SalesforceConfig(
            instance_url="https://myorg.my.salesforce.com",
            client_id="3MVG9...",
            client_secret="ABC123...",
        ))

        leads = conn.soql_query("SELECT Id, Name FROM Lead WHERE Status = 'New' LIMIT 10")
    """

    def __init__(self, config: SalesforceConfig) -> None:
        self.config = config
        self._base_url = f"{config.instance_url}/services/data/{config.api_version}"

    def _auth_headers(self) -> dict[str, str]:
        if self.config.access_token:
            token = self.config.access_token
        else:
            token = SalesforceTokenManager.get_token(
                client_id=self.config.client_id,       # type: ignore[arg-type]
                client_secret=self.config.client_secret,  # type: ignore[arg-type]
                login_url=self.config.login_url,
            )
        return {"Authorization": f"Bearer {token}"}

    # --- SOQL -----------------------------------------------------------------

    def soql_query(self, query: str) -> dict[str, Any]:
        """GET /query?q={soql} — returns {totalSize, done, records}."""
        return self._get("query", params={"q": query})

    def soql_query_all(self, query: str) -> list[dict[str, Any]]:
        """Paginate through all SOQL results, following nextRecordsUrl."""
        records: list[dict] = []
        result = self.soql_query(query)
        records.extend(result.get("records", []))
        next_url = result.get("nextRecordsUrl")
        while next_url and not result.get("done", True):
            result = self._get(next_url.split(f"/data/{self.config.api_version}/")[1])
            records.extend(result.get("records", []))
            next_url = result.get("nextRecordsUrl")
        return records

    # --- sObject CRUD ---------------------------------------------------------

    def get_record(self, sobject: str, record_id: str, fields: list[str] | None = None) -> dict[str, Any]:
        """GET /sobjects/{sobject}/{record_id}?fields=..."""
        params = {"fields": ",".join(fields)} if fields else None
        return self._get(f"sobjects/{sobject}/{record_id}", params=params)

    def create_record(self, sobject: str, data: dict[str, Any]) -> dict[str, Any]:
        """POST /sobjects/{sobject} — returns {id, success, errors}."""
        return self._post(f"sobjects/{sobject}", json=data)

    def update_record(self, sobject: str, record_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """PATCH /sobjects/{sobject}/{record_id} — Salesforce returns 204 No Content."""
        return self._patch(f"sobjects/{sobject}/{record_id}", json=data)

    def delete_record(self, sobject: str, record_id: str) -> dict[str, Any]:
        """DELETE /sobjects/{sobject}/{record_id} — returns 204 No Content."""
        return self._delete(f"sobjects/{sobject}/{record_id}")

    def upsert_record(
        self, sobject: str, external_id_field: str, external_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """PATCH /sobjects/{sobject}/{externalIdField}/{externalId} — upsert by external ID."""
        return self._patch(f"sobjects/{sobject}/{external_id_field}/{external_id}", json=data)

    # --- Describe -------------------------------------------------------------

    def describe_sobject(self, sobject: str) -> dict[str, Any]:
        """GET /sobjects/{sobject}/describe — returns full sObject metadata."""
        return self._get(f"sobjects/{sobject}/describe")

    # --- Composite ------------------------------------------------------------

    def composite_request(self, composite_request: list[dict[str, Any]]) -> dict[str, Any]:
        """POST /composite — batch up to 25 sub-requests in one round trip."""
        return self._post("composite", json={"compositeRequest": composite_request})
