"""Live integration tests for agents against the real Anthropic API.

Skipped when ANTHROPIC_API_KEY is the placeholder value or not set.
"""

from __future__ import annotations

import os
import pytest

_key = os.getenv("ANTHROPIC_API_KEY", "")
pytestmark = pytest.mark.skipif(
    not _key or _key.startswith("sk-test"),
    reason="Real ANTHROPIC_API_KEY not configured",
)

from agentic_erp.agents.order_agent import OrderProcessingAgent
from agentic_erp.agents.inventory_agent import InventoryAgent
from agentic_erp.patterns.multi_agent import MultiAgentOrchestrator


def test_order_agent_live():
    agent = OrderProcessingAgent()
    result = agent.run("What is the status of order ORD-001?")
    assert isinstance(result, str) and len(result) > 0


def test_inventory_agent_live():
    agent = InventoryAgent()
    result = agent.run("List items that need replenishment.")
    assert isinstance(result, str) and len(result) > 0


def test_multi_agent_orchestrator_live():
    orch = MultiAgentOrchestrator()
    results = orch.run("Check order ORD-002 and scan inventory for low stock.")
    assert "order_agent" in results
    assert "inventory_agent" in results
