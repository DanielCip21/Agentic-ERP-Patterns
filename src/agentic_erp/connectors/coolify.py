"""Coolify deployment connector.

Manages self-hosted deployments via the Coolify API.
Coolify is an open-source Heroku/Netlify alternative.

Docs: https://coolify.io/docs/api-reference/
"""

from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError


class CoolifyConnector:
    """Client for the Coolify REST API."""

    def __init__(self, base_url: str = "http://localhost:8000", api_token: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}",
        }

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        url = f"{self.base_url}/api/v1{path}"
        data = json.dumps(body).encode() if body else None
        req = Request(url, data=data, headers=self._headers, method=method)
        try:
            with urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except URLError as e:
            return {"error": str(e), "url": url}

    def list_projects(self) -> list[dict]:
        result = self._request("GET", "/projects")
        return result if isinstance(result, list) else result.get("data", [])

    def get_project(self, project_id: str) -> dict:
        return self._request("GET", f"/projects/{project_id}")

    def list_services(self, project_id: str) -> list[dict]:
        result = self._request("GET", f"/projects/{project_id}/services")
        return result if isinstance(result, list) else result.get("data", [])

    def deploy_service(self, service_id: str) -> dict:
        """Trigger a new deployment for a service."""
        return self._request("POST", f"/services/{service_id}/deploy")

    def get_deployment_status(self, deployment_id: str) -> dict:
        return self._request("GET", f"/deployments/{deployment_id}")

    def restart_service(self, service_id: str) -> dict:
        return self._request("POST", f"/services/{service_id}/restart")

    def get_service_logs(self, service_id: str, lines: int = 100) -> dict:
        return self._request("GET", f"/services/{service_id}/logs?lines={lines}")

    def get_stack_health(self) -> dict[str, Any]:
        """Return a health summary across all ERP/CRM projects."""
        projects = self.list_projects()
        if isinstance(projects, dict) and "error" in projects:
            return projects
        summary: dict[str, Any] = {"projects": [], "total": len(projects)}
        for p in projects:
            summary["projects"].append({
                "name": p.get("name"),
                "id": p.get("id"),
                "status": p.get("status", "unknown"),
            })
        return summary


# ERP/CRM service IDs in Coolify (set via environment variables in production)
ERP_SERVICES = {
    "erp_api": "erp-api-service",
    "crm_api": "crm-api-service",
    "n8n": "n8n-automation-service",
    "uptime_kuma": "uptime-kuma-service",
    "postgres": "postgres-db-service",
    "redis": "redis-cache-service",
}
