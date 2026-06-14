"""Unit tests for simulated ERP tools — no API calls required."""

import pytest
from agentic_erp.tools import erp_tools


def test_get_order_found():
    order = erp_tools.get_order("ORD-001")
    assert order["id"] == "ORD-001"
    assert order["customer"] == "Contoso Ltd"


def test_get_order_not_found():
    result = erp_tools.get_order("ORD-999")
    assert "error" in result


def test_update_order_status_valid():
    result = erp_tools.update_order_status("ORD-001", "processing")
    assert result["status"] == "processing"
    assert result["order_id"] == "ORD-001"


def test_update_order_status_invalid():
    result = erp_tools.update_order_status("ORD-001", "flying")
    assert "error" in result


def test_check_inventory_found():
    item = erp_tools.check_inventory("SKU-A")
    assert item["sku"] == "SKU-A"
    assert "on_hand" in item
    assert "below_reorder_point" in item


def test_check_inventory_not_found():
    result = erp_tools.check_inventory("SKU-UNKNOWN")
    assert "error" in result


def test_list_low_stock_items():
    items = erp_tools.list_low_stock_items()
    assert isinstance(items, list)
    for item in items:
        assert item["on_hand"] < item["reorder_point"]
        assert "shortage" in item


def test_create_purchase_order():
    before = erp_tools._INVENTORY["SKU-B"]["on_hand"]
    result = erp_tools.create_purchase_order("SKU-B", 50, "Acme Supplies")
    assert "po_id" in result
    assert result["sku"] == "SKU-B"
    assert result["quantity"] == 50
    assert result["status"] == "submitted"
    assert erp_tools._INVENTORY["SKU-B"]["on_hand"] == before + 50


def test_create_purchase_order_unknown_sku():
    result = erp_tools.create_purchase_order("SKU-FAKE", 10)
    assert "error" in result


# ---------------------------------------------------------------------------
# Fixed Assets tools
# ---------------------------------------------------------------------------

from agentic_erp.tools import fixed_assets_tools


def test_get_asset_found():
    asset = fixed_assets_tools.get_asset("AST-001")
    assert asset["asset_id"] == "AST-001"
    assert asset["name"] == "Corporate Office Building"
    assert "book_value" in asset
    assert "accumulated_depreciation" in asset


def test_get_asset_not_found():
    result = fixed_assets_tools.get_asset("AST-999")
    assert "error" in result


def test_get_asset_ifrs16_flag():
    asset = fixed_assets_tools.get_asset("AST-005")
    assert asset["ifrs16_lease"] is True
    assert "compliance_flag" in asset


def test_calculate_depreciation_straight_line():
    result = fixed_assets_tools.calculate_depreciation("AST-001", "2026-06")
    assert result["depreciation_amount"] > 0
    assert result["depreciation_method"] == "straight_line"
    assert result["book_value_after"] < result["book_value_before"]


def test_calculate_depreciation_declining_balance():
    result = fixed_assets_tools.calculate_depreciation("AST-002", "2026-06")
    assert result["depreciation_amount"] > 0
    assert result["depreciation_method"] == "declining_balance"


def test_calculate_depreciation_fully_depreciated():
    result = fixed_assets_tools.calculate_depreciation("AST-003", "2026-06")
    assert result["depreciation_amount"] == 0.00
    assert "note" in result


def test_calculate_depreciation_unknown_asset():
    result = fixed_assets_tools.calculate_depreciation("AST-999", "2026-06")
    assert "error" in result


def test_post_depreciation_journal():
    before_bv = fixed_assets_tools._ASSETS["AST-001"]["book_value"]
    result = fixed_assets_tools.post_depreciation_journal("AST-001", "2026-06", 9479.17)
    assert "journal_id" in result
    assert result["journal_id"].startswith("DEP-")
    assert result["status"] == "posted"
    assert result["debit_account"] == "6100 – Depreciation Expense"
    assert fixed_assets_tools._ASSETS["AST-001"]["book_value"] < before_bv


def test_post_depreciation_journal_negative_amount():
    result = fixed_assets_tools.post_depreciation_journal("AST-001", "2026-06", -100)
    assert "error" in result


def test_post_depreciation_journal_unknown_asset():
    result = fixed_assets_tools.post_depreciation_journal("AST-999", "2026-06", 100)
    assert "error" in result


def test_record_asset_disposal_gain():
    result = fixed_assets_tools.record_asset_disposal("AST-002", "2026-06-14", 80_000.00)
    assert "disposal_id" in result
    assert result["result"] == "GAIN"
    assert result["gain_loss"] > 0
    assert fixed_assets_tools._ASSETS["AST-002"]["status"] == "disposed"


def test_record_asset_disposal_already_disposed():
    result = fixed_assets_tools.record_asset_disposal("AST-002", "2026-06-14", 0)
    assert "error" in result


def test_record_asset_disposal_unknown_asset():
    result = fixed_assets_tools.record_asset_disposal("AST-999", "2026-06-14", 0)
    assert "error" in result


def test_revalue_asset_upward():
    result = fixed_assets_tools.revalue_asset("AST-001", 3_000_000.00, "2026-06-14")
    assert result["direction"] == "UPWARD"
    assert result["book_value_after"] == 3_000_000.00
    assert "Revaluation Surplus" in result["gl_account"]


def test_revalue_asset_downward():
    result = fixed_assets_tools.revalue_asset("AST-001", 2_000_000.00, "2026-06-14")
    assert result["direction"] == "DOWNWARD"
    assert result["adjustment"] < 0


def test_revalue_asset_negative_value():
    result = fixed_assets_tools.revalue_asset("AST-001", -1, "2026-06-14")
    assert "error" in result


def test_revalue_asset_unknown():
    result = fixed_assets_tools.revalue_asset("AST-999", 100, "2026-06-14")
    assert "error" in result


def test_list_fully_depreciated_assets():
    assets = fixed_assets_tools.list_fully_depreciated_assets()
    assert isinstance(assets, list)
    assert len(assets) >= 1
    for a in assets:
        assert "recommendation" in a
        assert "years_in_service" in a


def test_generate_asset_register():
    register = fixed_assets_tools.generate_asset_register()
    assert "assets" in register
    assert "totals" in register
    assert register["total_assets"] == len(register["assets"])
    totals = register["totals"]
    assert totals["gross_cost"] > 0
    assert totals["net_book_value"] >= 0
    assert totals["accumulated_depreciation"] >= 0
