"""n8n workflow connector.

Triggers and monitors n8n workflows via its REST API.
Self-hosted n8n is deployed via Coolify (see deploy/docker-compose.yml).

Docs: https://docs.n8n.io/api/
"""

from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError


class N8NConnector:
    """Client for the n8n REST API."""

    def __init__(self, base_url: str = "http://localhost:5678", api_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self._headers = {
            "Content-Type": "application/json",
            "X-N8N-API-KEY": api_key,
        }

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        url = f"{self.base_url}/api/v1{path}"
        data = json.dumps(body).encode() if body else None
        req = Request(url, data=data, headers=self._headers, method=method)
        try:
            with urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except URLError as e:
            return {"error": str(e), "url": url}

    def list_workflows(self) -> list[dict]:
        result = self._request("GET", "/workflows")
        return result.get("data", result)

    def get_workflow(self, workflow_id: str) -> dict:
        return self._request("GET", f"/workflows/{workflow_id}")

    def trigger_webhook_workflow(self, webhook_path: str, payload: dict) -> dict:
        """Trigger a webhook-triggered n8n workflow."""
        url = f"{self.base_url}/webhook/{webhook_path.lstrip('/')}"
        data = json.dumps(payload).encode()
        req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except URLError as e:
            return {"error": str(e), "webhook_path": webhook_path}

    def get_execution(self, execution_id: str) -> dict:
        return self._request("GET", f"/executions/{execution_id}")

    def list_executions(self, workflow_id: str | None = None, limit: int = 20) -> list[dict]:
        path = f"/executions?limit={limit}"
        if workflow_id:
            path += f"&workflowId={workflow_id}"
        result = self._request("GET", path)
        return result.get("data", result)


# Pre-defined webhook paths matching the workflows in deploy/n8n/workflows/
WEBHOOK_PATHS = {
    "erp_order_pipeline": "erp/order-pipeline",
    "crm_lead_nurturing": "crm/lead-nurturing",
    "inventory_alert": "erp/inventory-alert",
    "customer_health_check": "crm/health-check",
    "invoice_approval": "erp/invoice-approval",
}
