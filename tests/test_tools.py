"""Unit tests for simulated ERP tools — no API calls required."""

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
