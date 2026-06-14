"""Integration-style tests for agents — Anthropic client is mocked."""

import json
import pytest
from unittest.mock import MagicMock, patch
from agentic_erp.agents.order_agent import OrderProcessingAgent
from agentic_erp.agents.inventory_agent import InventoryAgent
from agentic_erp.agents.fixed_assets_agent import FixedAssetsAgent
from agentic_erp.patterns.multi_agent import MultiAgentOrchestrator, ERPOrchestrator
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


def _make_tool_then_text_response(tool_name: str, tool_inputs: dict, tool_use_id: str, final_text: str):
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
        client.messages.create.return_value = _make_text_response("Order ORD-001 is in pending status.")
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
            "list_low_stock_items", {}, "tu_xyz", "SKU-B is below reorder point. PO created."
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


class TestFixedAssetsAgent:
    def test_direct_text_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("All assets are accounted for.")
        agent = FixedAssetsAgent(client=client)
        result = agent.run("Show the asset register.")
        assert isinstance(result, str)

    def test_get_asset_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "get_asset", {"asset_id": "AST-001"}, "tu_ast1", "Corporate Office Building has NBV of $2.4M."
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = FixedAssetsAgent(client=client)
        result = agent.run("Get details for AST-001.")
        assert client.messages.create.call_count == 2
        assert isinstance(result, str)

    def test_calculate_depreciation_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "calculate_depreciation",
            {"asset_id": "AST-001", "period": "2026-06"},
            "tu_dep1",
            "Monthly depreciation for AST-001 is $9,479.17.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = FixedAssetsAgent(client=client)
        result = agent.run("Calculate June 2026 depreciation for AST-001.")
        assert isinstance(result, str)

    def test_post_depreciation_journal_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "post_depreciation_journal",
            {"asset_id": "AST-001", "period": "2026-06", "amount": 9479.17},
            "tu_dep2",
            "Depreciation journal DEP-12345 posted for AST-001.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = FixedAssetsAgent(client=client)
        result = agent.run("Post depreciation for AST-001 for June 2026.")
        assert isinstance(result, str)

    def test_list_fully_depreciated_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "list_fully_depreciated_assets",
            {},
            "tu_fd1",
            "AST-003 and AST-004 are fully depreciated and still in service.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = FixedAssetsAgent(client=client)
        result = agent.run("List all fully depreciated assets.")
        assert isinstance(result, str)

    def test_generate_asset_register_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "generate_asset_register",
            {},
            "tu_reg1",
            "Asset register generated: 5 assets, total NBV $2.57M.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = FixedAssetsAgent(client=client)
        result = agent.run("Generate the full asset register.")
        assert isinstance(result, str)

    def test_record_disposal_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "record_asset_disposal",
            {"asset_id": "AST-003", "disposal_date": "2026-06-14", "proceeds_usd": 0.0},
            "tu_dis1",
            "AST-003 written off. Gain/loss: $0.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = FixedAssetsAgent(client=client)
        result = agent.run("Write off AST-003 as of today.")
        assert isinstance(result, str)

    def test_revalue_asset_tool_call(self):
        client = MagicMock()
        tool_resp, text_resp = _make_tool_then_text_response(
            "revalue_asset",
            {"asset_id": "AST-001", "new_value_usd": 3_000_000.0, "revalue_date": "2026-06-14"},
            "tu_rev1",
            "AST-001 revalued to $3M. Revaluation surplus recorded.",
        )
        client.messages.create.side_effect = [tool_resp, text_resp]
        agent = FixedAssetsAgent(client=client)
        result = agent.run("Revalue the office building to $3M.")
        assert isinstance(result, str)

    def test_unknown_tool_returns_error(self):
        agent = FixedAssetsAgent(client=MagicMock())
        result = agent._dispatch_tool("audit_magic", {})
        assert "error" in result


class TestERPOrchestrator:
    def test_routes_fixed_assets_depreciation(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("Depreciation posted.")
        orch = ERPOrchestrator(client=client)
        results = orch.run("Calculate depreciation for all assets this month")
        assert "fixed_assets_agent" in results
        assert "order_agent" not in results
        assert "inventory_agent" not in results

    def test_routes_fixed_assets_disposal(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("Asset disposed.")
        orch = ERPOrchestrator(client=client)
        results = orch.run("Record disposal of old machinery")
        assert "fixed_assets_agent" in results

    def test_routes_fixed_assets_nbv(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("NBV report ready.")
        orch = ERPOrchestrator(client=client)
        results = orch.run("Show the NBV for all property assets")
        assert "fixed_assets_agent" in results

    def test_routes_order_task_unchanged(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("Order processed.")
        orch = ERPOrchestrator(client=client)
        results = orch.run("Process order ORD-001")
        assert "order_agent" in results
        assert "fixed_assets_agent" not in results

    def test_routes_ambiguous_task_to_order_and_inventory(self):
        client = MagicMock()
        client.messages.create.return_value = _make_text_response("Done.")
        orch = ERPOrchestrator(client=client)
        results = orch.run("Run the daily ERP summary")
        assert "order_agent" in results
        assert "inventory_agent" in results
