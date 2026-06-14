"""Simulated D365 Finance Fixed Assets tool implementations."""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any


_ASSETS: dict[str, dict] = {
    "AST-001": {
        "asset_id": "AST-001",
        "name": "Corporate Office Building",
        "category": "Property",
        "cost": 5_000_000.00,
        "acquisition_date": "2010-01-15",
        "useful_life_years": 40,
        "depreciation_method": "straight_line",
        "salvage_value": 500_000.00,
        "accumulated_depreciation": 2_062_500.00,
        "book_value": 2_437_500.00,
        "status": "active",
        "ifrs16_lease": False,
    },
    "AST-002": {
        "asset_id": "AST-002",
        "name": "CNC Manufacturing Equipment",
        "category": "Machinery",
        "cost": 250_000.00,
        "acquisition_date": "2020-06-01",
        "useful_life_years": 10,
        "depreciation_method": "declining_balance",
        "salvage_value": 10_000.00,
        "accumulated_depreciation": 184_508.16,
        "book_value": 65_491.84,
        "status": "active",
        "ifrs16_lease": False,
    },
    "AST-003": {
        "asset_id": "AST-003",
        "name": "Company Fleet Vehicle",
        "category": "Vehicles",
        "cost": 45_000.00,
        "acquisition_date": "2018-03-01",
        "useful_life_years": 5,
        "depreciation_method": "straight_line",
        "salvage_value": 0.00,
        "accumulated_depreciation": 45_000.00,
        "book_value": 0.00,
        "status": "active",
        "ifrs16_lease": False,
    },
    "AST-004": {
        "asset_id": "AST-004",
        "name": "Server Infrastructure",
        "category": "IT Equipment",
        "cost": 15_000.00,
        "acquisition_date": "2023-01-10",
        "useful_life_years": 3,
        "depreciation_method": "straight_line",
        "salvage_value": 0.00,
        "accumulated_depreciation": 15_000.00,
        "book_value": 0.00,
        "status": "active",
        "ifrs16_lease": False,
    },
    "AST-005": {
        "asset_id": "AST-005",
        "name": "Office Leasehold Improvements",
        "category": "Leasehold",
        "cost": 120_000.00,
        "acquisition_date": "2022-04-01",
        "useful_life_years": 10,
        "depreciation_method": "straight_line",
        "salvage_value": 0.00,
        "accumulated_depreciation": 50_400.00,
        "book_value": 69_600.00,
        "status": "active",
        "ifrs16_lease": True,
    },
}

_DEPRECIATION_JOURNALS: list[dict] = []
_DISPOSAL_RECORDS: list[dict] = []


def get_asset(asset_id: str) -> dict[str, Any]:
    asset = _ASSETS.get(asset_id)
    if not asset:
        return {"error": f"Asset {asset_id} not found"}
    result = dict(asset)
    if asset["ifrs16_lease"]:
        result["compliance_flag"] = "IFRS 16 / ASC 842 — right-of-use asset review required"
    return result


def calculate_depreciation(asset_id: str, period: str) -> dict[str, Any]:
    """Calculate monthly depreciation for an asset for a given period (YYYY-MM)."""
    asset = _ASSETS.get(asset_id)
    if not asset:
        return {"error": f"Asset {asset_id} not found"}
    if asset["book_value"] <= 0:
        return {
            "asset_id": asset_id,
            "period": period,
            "depreciation_amount": 0.00,
            "note": "Asset is fully depreciated — no further depreciation",
        }

    depreciable_base = asset["cost"] - asset["salvage_value"]

    if asset["depreciation_method"] == "straight_line":
        monthly = round(depreciable_base / (asset["useful_life_years"] * 12), 2)
    else:  # declining_balance
        annual_rate = 2.0 / asset["useful_life_years"]
        monthly = round(asset["book_value"] * annual_rate / 12, 2)

    return {
        "asset_id": asset_id,
        "asset_name": asset["name"],
        "period": period,
        "depreciation_method": asset["depreciation_method"],
        "depreciation_amount": monthly,
        "book_value_before": asset["book_value"],
        "book_value_after": round(max(0.0, asset["book_value"] - monthly), 2),
    }


def post_depreciation_journal(asset_id: str, period: str, amount: float) -> dict[str, Any]:
    """Post a depreciation journal entry to GL and update the asset's book value."""
    asset = _ASSETS.get(asset_id)
    if not asset:
        return {"error": f"Asset {asset_id} not found"}
    if amount < 0:
        return {"error": "Depreciation amount cannot be negative"}

    journal_id = f"DEP-{random.randint(10000, 99999)}"
    entry = {
        "journal_id": journal_id,
        "asset_id": asset_id,
        "asset_name": asset["name"],
        "period": period,
        "debit_account": "6100 – Depreciation Expense",
        "credit_account": "1500 – Accumulated Depreciation",
        "amount": amount,
        "posted_at": datetime.utcnow().isoformat(),
        "status": "posted",
    }
    _DEPRECIATION_JOURNALS.append(entry)
    asset["accumulated_depreciation"] = round(asset["accumulated_depreciation"] + amount, 2)
    asset["book_value"] = round(max(0.0, asset["book_value"] - amount), 2)
    return entry


def record_asset_disposal(asset_id: str, disposal_date: str, proceeds_usd: float) -> dict[str, Any]:
    """Record an asset sale or write-off and calculate gain or loss."""
    asset = _ASSETS.get(asset_id)
    if not asset:
        return {"error": f"Asset {asset_id} not found"}
    if asset["status"] == "disposed":
        return {"error": f"Asset {asset_id} is already disposed"}

    book_value = asset["book_value"]
    gain_loss = round(proceeds_usd - book_value, 2)
    disposal = {
        "disposal_id": f"DIS-{random.randint(1000, 9999)}",
        "asset_id": asset_id,
        "asset_name": asset["name"],
        "disposal_date": disposal_date,
        "proceeds_usd": proceeds_usd,
        "book_value_at_disposal": book_value,
        "gain_loss": gain_loss,
        "result": "GAIN" if gain_loss >= 0 else "LOSS",
        "gl_entries": [
            {"account": "1000 – Cash / Receivable", "debit": proceeds_usd},
            {"account": "1500 – Accumulated Depreciation", "debit": asset["accumulated_depreciation"]},
            {"account": "1400 – Fixed Asset Cost", "credit": asset["cost"]},
            {"account": "7100 – Gain/Loss on Disposal", "amount": gain_loss},
        ],
        "disposed_at": datetime.utcnow().isoformat(),
    }
    _DISPOSAL_RECORDS.append(disposal)
    asset["status"] = "disposed"
    asset["book_value"] = 0.00
    return disposal


def revalue_asset(asset_id: str, new_value_usd: float, revalue_date: str) -> dict[str, Any]:
    """Apply a revaluation adjustment to an asset's book value (IAS 16)."""
    asset = _ASSETS.get(asset_id)
    if not asset:
        return {"error": f"Asset {asset_id} not found"}
    if new_value_usd < 0:
        return {"error": "Revalued amount cannot be negative"}

    old_book_value = asset["book_value"]
    adjustment = round(new_value_usd - old_book_value, 2)
    asset["book_value"] = round(new_value_usd, 2)
    if adjustment > 0:
        asset["cost"] = round(asset["cost"] + adjustment, 2)

    return {
        "asset_id": asset_id,
        "asset_name": asset["name"],
        "revalue_date": revalue_date,
        "book_value_before": old_book_value,
        "book_value_after": new_value_usd,
        "adjustment": adjustment,
        "direction": "UPWARD" if adjustment >= 0 else "DOWNWARD",
        "gl_account": "3200 – Revaluation Surplus" if adjustment >= 0 else "7200 – Revaluation Loss",
        "ifrs_note": "IFRS 16 lease asset revaluation" if asset["ifrs16_lease"] else "IAS 16 revaluation model applied",
    }


def list_fully_depreciated_assets() -> list[dict[str, Any]]:
    """Return all active assets with zero net book value still in service."""
    return [
        {
            "asset_id": asset_id,
            "name": asset["name"],
            "category": asset["category"],
            "cost": asset["cost"],
            "acquisition_date": asset["acquisition_date"],
            "useful_life_years": asset["useful_life_years"],
            "years_in_service": round(
                (datetime.utcnow() - datetime.fromisoformat(asset["acquisition_date"])).days / 365.25, 1
            ),
            "recommendation": "Review for disposal, extension of useful life, or write-off",
        }
        for asset_id, asset in _ASSETS.items()
        if asset["book_value"] <= 0 and asset["status"] == "active"
    ]


def generate_asset_register() -> dict[str, Any]:
    """Generate the full fixed asset register with NBV and accumulated depreciation."""
    register = []
    total_cost = 0.0
    total_acc_dep = 0.0
    total_nbv = 0.0

    for asset in _ASSETS.values():
        register.append({
            "asset_id": asset["asset_id"],
            "name": asset["name"],
            "category": asset["category"],
            "cost": asset["cost"],
            "salvage_value": asset["salvage_value"],
            "accumulated_depreciation": asset["accumulated_depreciation"],
            "net_book_value": asset["book_value"],
            "depreciation_method": asset["depreciation_method"],
            "useful_life_years": asset["useful_life_years"],
            "acquisition_date": asset["acquisition_date"],
            "status": asset["status"],
            "ifrs16_lease": asset["ifrs16_lease"],
        })
        total_cost += asset["cost"]
        total_acc_dep += asset["accumulated_depreciation"]
        total_nbv += asset["book_value"]

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "total_assets": len(register),
        "totals": {
            "gross_cost": round(total_cost, 2),
            "accumulated_depreciation": round(total_acc_dep, 2),
            "net_book_value": round(total_nbv, 2),
        },
        "assets": register,
    }
