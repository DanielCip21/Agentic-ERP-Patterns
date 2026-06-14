"""Pattern: Orchestrator → Specialist multi-agent pipeline.

The orchestrator receives a high-level ERP task and routes sub-tasks to specialist
agents (order, inventory). Each specialist runs its own agentic loop independently.
"""

from __future__ import annotations

from agentic_erp.agents.order_agent import OrderProcessingAgent
from agentic_erp.agents.inventory_agent import InventoryAgent
from agentic_erp.agents.fixed_assets_agent import FixedAssetsAgent


class MultiAgentOrchestrator:
    """Routes tasks to specialist agents and aggregates their results."""

    def __init__(self, **agent_kwargs) -> None:
        self._order_agent = OrderProcessingAgent(**agent_kwargs)
        self._inventory_agent = InventoryAgent(**agent_kwargs)

    def run(self, task: str) -> dict[str, str]:
        """Classify the task and dispatch to the appropriate specialist(s).

        Returns a dict mapping agent name → response.
        """
        task_lower = task.lower()
        results: dict[str, str] = {}

        words = set(task_lower.split())
        needs_order = bool(words & {"order", "orders", "shipment", "delivery", "customer", "customers"})
        needs_inventory = any(kw in task_lower for kw in ("inventory", "stock", "replenish", "reorder", "purchase"))

        if not needs_order and not needs_inventory:
            needs_order = True
            needs_inventory = True

        if needs_order:
            results["order_agent"] = self._order_agent.run(task)
        if needs_inventory:
            results["inventory_agent"] = self._inventory_agent.run(task)

        return results


_FIXED_ASSETS_KEYWORDS = (
    "fixed asset", "depreciation", "depreciate", "disposal", "dispose",
    "revaluation", "revalue", "nbv", "net book value", "useful life",
    "asset register", "fully depreciated",
)


class ERPOrchestrator:
    """Extended orchestrator that routes tasks across all specialist ERP agents."""

    def __init__(self, **agent_kwargs) -> None:
        self._agents: dict[str, object] = {
            "order": OrderProcessingAgent(**agent_kwargs),
            "inventory": InventoryAgent(**agent_kwargs),
            "fixed_assets": FixedAssetsAgent(**agent_kwargs),
        }

    def run(self, task: str) -> dict[str, str]:
        """Route the task to the appropriate specialist agent(s) and return results."""
        task_lower = task.lower()
        results: dict[str, str] = {}

        words = set(task_lower.split())
        needs_order = bool(words & {"order", "orders", "shipment", "delivery", "customer", "customers"})
        needs_inventory = any(kw in task_lower for kw in ("inventory", "stock", "replenish", "reorder", "purchase"))
        needs_fixed_assets = any(kw in task_lower for kw in _FIXED_ASSETS_KEYWORDS)

        if not needs_order and not needs_inventory and not needs_fixed_assets:
            needs_order = True
            needs_inventory = True

        if needs_order:
            results["order_agent"] = self._agents["order"].run(task)
        if needs_inventory:
            results["inventory_agent"] = self._agents["inventory"].run(task)
        if needs_fixed_assets:
            results["fixed_assets_agent"] = self._agents["fixed_assets"].run(task)

        return results
