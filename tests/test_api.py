"""Tests for the FastAPI server — agents are mocked so no Anthropic API calls are made."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from agentic_erp.api import server as erp_server
from agentic_erp.api.server import app, _AGENT_REGISTRY

client = TestClient(app)

_ALL_DOMAINS = list(_AGENT_REGISTRY.keys())


@contextmanager
def _patch_agent(domain: str, result: str = "Agent response."):
    """Replace a registry entry with a mock agent for the duration of the block."""
    mock_instance = MagicMock()
    mock_instance.run.return_value = result
    mock_cls = MagicMock(return_value=mock_instance)
    patched = {**erp_server._AGENT_REGISTRY, domain: {"cls": mock_cls, "description": "mocked"}}
    with patch.object(erp_server, "_AGENT_REGISTRY", patched):
        yield


@contextmanager
def _patch_orchestrator(results: dict):
    """Replace the ERPOrchestrator with a mock for the duration of the block."""
    mock_orch = MagicMock()
    mock_orch.run.return_value = results
    with patch.object(erp_server, "ERPOrchestrator", return_value=mock_orch):
        yield


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"
        assert isinstance(data["agents"], int)
        assert data["agents"] == len(_AGENT_REGISTRY)


# ---------------------------------------------------------------------------
# /agents
# ---------------------------------------------------------------------------

class TestListAgents:
    def test_returns_all_domains(self):
        response = client.get("/agents")
        assert response.status_code == 200
        domains = [e["domain"] for e in response.json()]
        for domain in _ALL_DOMAINS:
            assert domain in domains

    def test_each_entry_has_description(self):
        for entry in client.get("/agents").json():
            assert "domain" in entry
            assert "description" in entry
            assert len(entry["description"]) > 0

    def test_fixed_assets_domain_listed(self):
        domains = [e["domain"] for e in client.get("/agents").json()]
        assert "fixed_assets" in domains


# ---------------------------------------------------------------------------
# POST /agents/{domain}/run
# ---------------------------------------------------------------------------

class TestRunAgent:
    def test_order_agent_returns_correct_shape(self):
        with _patch_agent("order", "Order processed."):
            response = client.post("/agents/order/run", json={"task": "Process order ORD-001"})
        assert response.status_code == 200
        data = response.json()
        assert data["domain"] == "order"
        assert data["result"] == "Order processed."
        assert isinstance(data["duration_ms"], float)

    def test_inventory_agent_success(self):
        with _patch_agent("inventory", "Stock checked."):
            response = client.post("/agents/inventory/run", json={"task": "Check stock levels"})
        assert response.status_code == 200
        assert response.json()["domain"] == "inventory"

    def test_fraud_agent_success(self):
        with _patch_agent("fraud", "No fraud found."):
            response = client.post("/agents/fraud/run", json={"task": "Scan ACC-01 for anomalies"})
        assert response.status_code == 200
        assert response.json()["domain"] == "fraud"

    def test_fixed_assets_agent_success(self):
        with _patch_agent("fixed_assets", "Depreciation posted."):
            response = client.post("/agents/fixed_assets/run", json={"task": "Run depreciation for June 2026"})
        assert response.status_code == 200
        assert response.json()["domain"] == "fixed_assets"

    def test_all_registered_domains_return_200(self):
        for domain in _ALL_DOMAINS:
            with _patch_agent(domain, "ok"):
                response = client.post(f"/agents/{domain}/run", json={"task": "daily health check"})
            assert response.status_code == 200, f"Domain '{domain}' returned {response.status_code}"

    def test_unknown_domain_returns_404(self):
        response = client.post("/agents/gl/run", json={"task": "reconcile GL for 2025-01"})
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_another_unknown_domain_returns_404(self):
        response = client.post("/agents/quantum/run", json={"task": "do something"})
        assert response.status_code == 404

    def test_empty_task_returns_422(self):
        response = client.post("/agents/order/run", json={"task": ""})
        assert response.status_code == 422

    def test_missing_task_field_returns_422(self):
        response = client.post("/agents/order/run", json={})
        assert response.status_code == 422

    def test_response_includes_duration_ms(self):
        with _patch_agent("compliance", "Compliance check done."):
            response = client.post("/agents/compliance/run", json={"task": "Check US compliance"})
        assert response.status_code == 200
        assert response.json()["duration_ms"] >= 0


# ---------------------------------------------------------------------------
# POST /orchestrator/run
# ---------------------------------------------------------------------------

class TestRunOrchestrator:
    def test_orchestrator_returns_results_dict(self):
        with _patch_orchestrator({"order_agent": "Orders reviewed.", "inventory_agent": "Stock checked."}):
            response = client.post("/orchestrator/run", json={"task": "Run daily ERP summary"})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], dict)

    def test_orchestrator_fixed_assets_routing(self):
        with _patch_orchestrator({"fixed_assets_agent": "Depreciation posted for all assets."}):
            response = client.post("/orchestrator/run", json={"task": "Post depreciation for all assets"})
        assert response.status_code == 200
        assert "fixed_assets_agent" in response.json()["results"]

    def test_orchestrator_empty_task_returns_422(self):
        response = client.post("/orchestrator/run", json={"task": ""})
        assert response.status_code == 422

    def test_orchestrator_missing_task_returns_422(self):
        response = client.post("/orchestrator/run", json={})
        assert response.status_code == 422
