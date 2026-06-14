"""Uptime Kuma health monitoring connector.

Connects to a self-hosted Uptime Kuma instance (deployed via Coolify).
Uses the Uptime Kuma status page API and push monitors.

Docs: https://github.com/louislam/uptime-kuma
"""

from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError


class UptimeKumaConnector:
    """Client for Uptime Kuma's status and push endpoints."""

    def __init__(self, base_url: str = "http://localhost:3001") -> None:
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str) -> dict:
        url = f"{self.base_url}{path}"
        req = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except URLError as e:
            return {"error": str(e), "url": url}

    def get_status_page(self, slug: str = "erp-crm") -> dict:
        """Fetch a public status page summary."""
        return self._get(f"/api/status-page/{slug}")

    def push_heartbeat(self, push_token: str, status: str = "up", msg: str = "OK", ping: int = 0) -> dict:
        """Send a heartbeat to a push-type monitor."""
        url = f"{self.base_url}/api/push/{push_token}?status={status}&msg={msg}&ping={ping}"
        req = Request(url)
        try:
            with urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except URLError as e:
            return {"error": str(e)}

    def get_all_monitor_status(self) -> dict[str, Any]:
        """Return a simplified health summary across all monitored services."""
        page = self.get_status_page()
        if "error" in page:
            return page
        monitors = page.get("publicGroupList", [])
        result: dict[str, Any] = {"services": [], "overall": "up"}
        for group in monitors:
            for monitor in group.get("monitorList", []):
                entry = {
                    "name": monitor.get("name"),
                    "status": "up" if monitor.get("active") else "down",
                    "uptime_24h": monitor.get("uptime", {}).get("24", 0),
                    "avg_response_ms": monitor.get("avgPing"),
                }
                result["services"].append(entry)
                if entry["status"] == "down":
                    result["overall"] = "degraded"
        return result


# Service monitor names that map to ERP/CRM components
ERP_MONITORS = {
    "erp-api": "ERP API",
    "crm-api": "CRM API",
    "n8n-automation": "n8n Workflow Engine",
    "coolify-dashboard": "Coolify Deployment Dashboard",
    "postgres-db": "PostgreSQL Database",
    "redis-cache": "Redis Cache",
}
