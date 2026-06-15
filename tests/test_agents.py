"""Integration-style tests for agents — Anthropic client is mocked."""

from unittest.mock import MagicMock
from agentic_erp.agents.order_agent import OrderProcessingAgent
from agentic_erp.agents.inventory_agent import InventoryAgent
from agentic_erp.patterns.multi_agent import MultiAgentOrchestrator
from agentic_erp.patterns.human_in_loop import HumanInLoopAgent


def _make_text_response(text: str):
    """Build a minimal mock Anthropic response that returns a text block."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    return response


def _make_tool_then_text_response(
    tool_name: str, tool_inputs: dict, tool_use_id: str, final_text: str
):
    """Simulate one tool-use round followed by an end_turn text response."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.input = tool_inputs
    tool_block.id = tool_use_id

    tool_response = MagicMock()
    tool_response.stop_reason = "tool_use"
    tool_response.content = [tool_block]

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = final_text

    text_response = MagicMock()
    text_response.stop_reason = "end_turn"
    text_response.content = [text_block]

    return tool_response, text_response


class TestOrderProcessingAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response(
            "Order ORD-001 is in pending status."
        )
        agent = OrderProcessingAgent(client=client)
        result = agent.run("What is the status of order ORD-001?")
        assert "pending" in result.lower() or "ORD-001" in result

    def test_tool_use_then_response(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "get_order", {"order_id": "ORD-001"}, "tu_abc", "Order ORD-001 is pending."
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = OrderProcessingAgent(client=client)
        result = agent.run("Get details for ORD-001")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)


class TestInventoryAgent:
    def test_low_stock_scan(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "list_low_stock_items",
            {},
            "tu_xyz",
            "SKU-B is below reorder point. PO created.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = InventoryAgent(client=client)
        result = agent.run("Check for low stock and replenish.")
        assert isinstance(result, str)


class TestMultiAgentOrchestrator:
    def test_routes_order_task(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("Order processed.")
        orch = MultiAgentOrchestrator(client=client)
        results = orch.run("Process order ORD-002")
        assert "order_agent" in results
        assert "inventory_agent" not in results

    def test_routes_inventory_task(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("Stock replenished.")
        orch = MultiAgentOrchestrator(client=client)
        results = orch.run("Check stock levels and reorder if needed")
        assert "inventory_agent" in results
        assert "order_agent" not in results

    def test_routes_ambiguous_task_to_both(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("Done.")
        orch = MultiAgentOrchestrator(client=client)
        results = orch.run("Run the daily ERP summary")
        assert "order_agent" in results
        assert "inventory_agent" in results


class TestHumanInLoopAgent:
    def test_approved_action_proceeds(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "update_order_status",
            {"order_id": "ORD-001", "status": "shipped"},
            "tu_ship",
            "Order ORD-001 shipped.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = HumanInLoopAgent(approval_callback=lambda *_: True, client=client)
        result = agent.run("Ship order ORD-001")
        assert isinstance(result, str)

    def test_rejected_action_blocked(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "update_order_status",
            {"order_id": "ORD-001", "status": "cancelled"},
            "tu_cancel",
            "Action was rejected.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        rejected_calls: list = []

        def tracking_callback(name, inputs):
            rejected_calls.append((name, inputs))
            return False

        agent = HumanInLoopAgent(approval_callback=tracking_callback, client=client)
        result = agent.run("Cancel order ORD-001")
        # Callback must have been triggered once with the right tool
        assert len(rejected_calls) == 1
        assert rejected_calls[0][0] == "update_order_status"
        assert rejected_calls[0][1]["status"] == "cancelled"
        assert isinstance(result, str)
