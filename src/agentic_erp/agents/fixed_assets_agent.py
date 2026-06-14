"""Pattern: Fixed Assets depreciation, disposal & revaluation automation agent."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import fixed_assets_tools

_TOOLS = [
    {
        "name": "get_asset",
        "description": "Retrieve asset details by asset ID including cost, book value, useful life, and depreciation method.",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "Asset ID (e.g. AST-001)"},
            },
            "required": ["asset_id"],
        },
    },
    {
        "name": "calculate_depreciation",
        "description": "Calculate the monthly depreciation amount for an asset using straight-line or declining-balance method.",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string"},
                "period": {"type": "string", "description": "Accounting period in YYYY-MM format (e.g. 2026-06)"},
            },
            "required": ["asset_id", "period"],
        },
    },
    {
        "name": "post_depreciation_journal",
        "description": "Post a depreciation journal entry to the General Ledger for the given asset and period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string"},
                "period": {"type": "string", "description": "Accounting period YYYY-MM"},
                "amount": {"type": "number", "description": "Depreciation amount in USD"},
            },
            "required": ["asset_id", "period", "amount"],
        },
    },
    {
        "name": "record_asset_disposal",
        "description": "Record the sale or write-off of a fixed asset and calculate the resulting gain or loss on disposal.",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string"},
                "disposal_date": {"type": "string", "description": "Date of disposal (YYYY-MM-DD)"},
                "proceeds_usd": {"type": "number", "description": "Sale proceeds in USD — use 0 for a write-off"},
            },
            "required": ["asset_id", "disposal_date", "proceeds_usd"],
        },
    },
    {
        "name": "revalue_asset",
        "description": "Apply an upward or downward revaluation adjustment to an asset's book value (e.g. property market revaluation under IAS 16).",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string"},
                "new_value_usd": {"type": "number", "description": "New book value in USD after revaluation"},
                "revalue_date": {"type": "string", "description": "Date of revaluation (YYYY-MM-DD)"},
            },
            "required": ["asset_id", "new_value_usd", "revalue_date"],
        },
    },
    {
        "name": "list_fully_depreciated_assets",
        "description": "List all active assets with zero net book value that are still in service — candidates for disposal or useful life extension.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "generate_asset_register",
        "description": "Generate the complete fixed asset register showing gross cost, accumulated depreciation, and net book value for every asset.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

_SYSTEM_PROMPT = """You are a Fixed Assets Accounting Agent for a global enterprise.
Your responsibilities:
1. Calculate and post monthly depreciation runs for all active assets.
2. Flag assets that have exceeded their useful life but remain on the books.
3. Recommend disposal, write-off, or extension of useful life for fully-depreciated assets.
4. Record asset disposals accurately, computing gain or loss against current book value.
5. Apply revaluation adjustments for properties and leased assets per IAS 16 / IFRS 16.
6. Generate the fixed asset register for audit and financial reporting.
Always note IFRS 16 / ASC 842 compliance flags for right-of-use lease assets.
Be precise — round amounts to two decimal places and cite GL account codes in every entry."""


class FixedAssetsAgent(BaseERPAgent):
    """Automates depreciation, disposal, and revaluation for the D365 Fixed Assets module."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_asset":
                return fixed_assets_tools.get_asset(**inputs)
            case "calculate_depreciation":
                return fixed_assets_tools.calculate_depreciation(**inputs)
            case "post_depreciation_journal":
                return fixed_assets_tools.post_depreciation_journal(**inputs)
            case "record_asset_disposal":
                return fixed_assets_tools.record_asset_disposal(**inputs)
            case "revalue_asset":
                return fixed_assets_tools.revalue_asset(**inputs)
            case "list_fully_depreciated_assets":
                return fixed_assets_tools.list_fully_depreciated_assets(**inputs)
            case "generate_asset_register":
                return fixed_assets_tools.generate_asset_register(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
