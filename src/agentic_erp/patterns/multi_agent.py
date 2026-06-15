"""Pattern: Orchestrator → Specialist multi-agent pipeline.

The orchestrator receives a high-level ERP task and routes sub-tasks to specialist
agents (order, inventory). Each specialist runs its own agentic loop independently.
"""

from __future__ import annotations

from agentic_erp.agents.order_agent import OrderProcessingAgent
from agentic_erp.agents.inventory_agent import InventoryAgent


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
        needs_order = bool(
            words & {"order", "orders", "shipment", "delivery", "customer", "customers"}
        )
        needs_inventory = any(
            kw in task_lower
            for kw in ("inventory", "stock", "replenish", "reorder", "purchase")
        )

        if not needs_order and not needs_inventory:
            needs_order = True
            needs_inventory = True

        if needs_order:
            results["order_agent"] = self._order_agent.run(task)
        if needs_inventory:
            results["inventory_agent"] = self._inventory_agent.run(task)

        return results
