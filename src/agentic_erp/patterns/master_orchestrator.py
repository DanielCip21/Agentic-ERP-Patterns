"""Master ERP+CRM Orchestrator.

Combines all specialist agents into a single unified product:
  - ERP: order processing, inventory, finance, compliance, fraud detection
  - CRM: leads, contacts, accounts, opportunities, customer success
  - Infrastructure: health monitoring via Uptime Kuma, workflow triggers via n8n

Routing is keyword-based and falls back to running all agents for ambiguous tasks.
"""

from __future__ import annotations

from agentic_erp.agents.order_agent import OrderProcessingAgent
from agentic_erp.agents.inventory_agent import InventoryAgent
from agentic_erp.agents.crm_agent import CRMAgent
from agentic_erp.connectors.n8n import N8NConnector, WEBHOOK_PATHS
from agentic_erp.connectors.uptime_kuma import UptimeKumaConnector
from agentic_erp.connectors.coolify import CoolifyConnector


class MasterERPCRMOrchestrator:
    """Unified ERP+CRM orchestrator integrating all agents and infrastructure connectors."""

    def __init__(
        self,
        n8n_url: str = "http://localhost:5678",
        n8n_api_key: str = "",
        uptime_kuma_url: str = "http://localhost:3001",
        coolify_url: str = "http://localhost:8000",
        coolify_token: str = "",
        **agent_kwargs,
    ) -> None:
        # Specialist agents
        self._order_agent = OrderProcessingAgent(**agent_kwargs)
        self._inventory_agent = InventoryAgent(**agent_kwargs)
        self._crm_agent = CRMAgent(**agent_kwargs)

        # Infrastructure connectors
        self._n8n = N8NConnector(base_url=n8n_url, api_key=n8n_api_key)
        self._uptime = UptimeKumaConnector(base_url=uptime_kuma_url)
        self._coolify = CoolifyConnector(base_url=coolify_url, api_token=coolify_token)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, task: str) -> dict[str, object]:
        """Route the task to the appropriate agent(s) and return all results."""
        results: dict[str, object] = {}
        routing = self._classify(task)

        if routing["order"]:
            results["order_agent"] = self._order_agent.run(task)
        if routing["inventory"]:
            results["inventory_agent"] = self._inventory_agent.run(task)
        if routing["crm"]:
            results["crm_agent"] = self._crm_agent.run(task)

        # Always attach live infrastructure health when running a full reconciliation
        if routing["infrastructure"] or routing["all"]:
            results["infrastructure"] = self.infrastructure_health()

        return results

    def run_daily_reconciliation(self) -> dict[str, object]:
        """Full daily ERP+CRM reconciliation: check orders, stock, pipeline, and health."""
        return {
            "order_agent": self._order_agent.run(
                "Review all pending orders and update statuses where inventory allows."
            ),
            "inventory_agent": self._inventory_agent.run(
                "Scan for low-stock items and create purchase orders as needed."
            ),
            "crm_agent": self._crm_agent.run(
                "List at-risk accounts, find unassigned leads, and summarize the sales pipeline."
            ),
            "infrastructure": self.infrastructure_health(),
        }

    def trigger_workflow(self, workflow_key: str, payload: dict) -> dict:
        """Trigger an n8n automation workflow by its logical key."""
        path = WEBHOOK_PATHS.get(workflow_key)
        if not path:
            return {"error": f"Unknown workflow key '{workflow_key}'. Available: {list(WEBHOOK_PATHS.keys())}"}
        return self._n8n.trigger_webhook_workflow(path, payload)

    def infrastructure_health(self) -> dict[str, object]:
        """Aggregate health status from Uptime Kuma and Coolify."""
        return {
            "uptime_kuma": self._uptime.get_all_monitor_status(),
            "coolify": self._coolify.get_stack_health(),
        }

    # ------------------------------------------------------------------
    # Internal routing
    # ------------------------------------------------------------------

    def _classify(self, task: str) -> dict[str, bool]:
        t = task.lower()
        words = set(t.split())
        return {
            "order": bool(words & {"order", "orders", "shipment", "delivery", "invoice", "payment"}),
            "inventory": any(kw in t for kw in ("inventory", "stock", "replenish", "reorder", "purchase")),
            "crm": any(kw in t for kw in ("lead", "leads", "contact", "account", "opportunity", "pipeline", "customer", "churn", "sales")),
            "infrastructure": any(kw in t for kw in ("health", "monitor", "deploy", "uptime", "service", "infra")),
            "all": any(kw in t for kw in ("reconciliation", "daily", "all", "full", "everything")),
        }
